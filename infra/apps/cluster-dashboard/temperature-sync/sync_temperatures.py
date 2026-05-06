from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CONFIG_PATH = Path(os.getenv("DASHBOARD_CONFIG_PATH", "/config/nodes.json"))
TOKEN_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
NAMESPACE_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
CA_PATH = Path("/var/run/secrets/kubernetes.io/serviceaccount/ca.crt")
SSH_USER = os.getenv("SSH_USER", "pi")
SSH_KEY_PATH = Path(os.getenv("SSH_KEY_PATH", "/ssh/id_ed25519"))
CONFIGMAP_NAME = os.getenv("CONFIGMAP_NAME", "cluster-dashboard-config")
TEMP_RE = re.compile(r"temp=([0-9]+(?:\.[0-9]+)?)'C")
TEMPERATURE_COMMANDS = (
    "vcgencmd measure_temp",
    "cat /sys/class/thermal/thermal_zone0/temp",
)
LOAD_AVERAGE_COMMAND = "cat /proc/loadavg"
UPTIME_COMMAND = "cat /proc/uptime"


def load_dashboard_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def parse_temperature_output(output: str) -> float:
    text = output.strip()
    match = TEMP_RE.search(text)
    if match:
        return float(match.group(1))

    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text):
        value = float(text)
        return value / 1000 if value > 1000 else value

    raise ValueError(f"unrecognized temperature output: {text!r}")


def parse_load_average_output(output: str) -> float:
    token = output.strip().split()[0]
    return float(token)


def parse_uptime_output(output: str) -> float:
    token = output.strip().split()[0]
    return float(token)


def format_uptime(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def run_remote_command(host: str, command: str) -> subprocess.CompletedProcess[str]:
    ssh_command = [
        "ssh",
        "-i",
        str(SSH_KEY_PATH),
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "UserKnownHostsFile=/tmp/known_hosts",
        "-o",
        "ConnectTimeout=5",
        f"{SSH_USER}@{host}",
        command,
    ]
    return subprocess.run(
        ssh_command,
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


def collect_metric(host: str, command: str, parser, label: str):
    try:
        result = run_remote_command(host, command)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{label}: command timed out") from error

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(f"{label}: {message}")

    try:
        return parser(result.stdout)
    except (IndexError, ValueError) as error:
        raise RuntimeError(f"{label}: {error}") from error


def collect_temperature(host: str) -> float:
    errors: list[str] = []
    for command in TEMPERATURE_COMMANDS:
        try:
            return round(collect_metric(host, command, parse_temperature_output, "temperature"), 1)
        except RuntimeError as error:
            errors.append(f"{command}: {error}")

    joined = "; ".join(errors)
    raise RuntimeError(joined)


def collect_node_metrics(node: dict) -> dict:
    host = node.get("ip")
    if not host:
        raise RuntimeError(f"node {node.get('name', '<unknown>')} is missing an IP address")

    temperature = collect_temperature(host)
    load_average = round(collect_metric(host, LOAD_AVERAGE_COMMAND, parse_load_average_output, "load average"), 2)
    uptime_seconds = collect_metric(host, UPTIME_COMMAND, parse_uptime_output, "uptime")

    return {
        "temperatureC": temperature,
        "loadAverage1m": load_average,
        "uptimeHuman": format_uptime(uptime_seconds),
    }


def collect_metrics(data: dict) -> tuple[dict, list[str], int]:
    failures: list[str] = []
    success_count = 0

    for node in data.get("nodes", []):
        try:
            node.update(collect_node_metrics(node))
            success_count += 1
        except RuntimeError as error:
            node.pop("temperatureC", None)
            node.pop("loadAverage1m", None)
            node.pop("uptimeHuman", None)
            failures.append(f"{node.get('name', node.get('ip', '<unknown>'))}: {error}")

    if success_count == 0:
        raise RuntimeError("metric collection failed for every configured node")

    data["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return data, failures, success_count


def patch_configmap(nodes_json: str) -> None:
    namespace = NAMESPACE_PATH.read_text().strip()
    token = TOKEN_PATH.read_text().strip()
    host = os.environ["KUBERNETES_SERVICE_HOST"]
    port = os.environ.get("KUBERNETES_SERVICE_PORT_HTTPS", os.environ.get("KUBERNETES_SERVICE_PORT", "443"))
    url = f"https://{host}:{port}/api/v1/namespaces/{namespace}/configmaps/{CONFIGMAP_NAME}"

    payload = json.dumps({"data": {"nodes.json": nodes_json}}).encode()
    request = Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/merge-patch+json",
        },
    )

    ssl_context = ssl.create_default_context(cafile=str(CA_PATH))
    try:
        with urlopen(request, context=ssl_context, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"configmap patch failed with HTTP {response.status}")
    except HTTPError as error:
        body = error.read().decode(errors="replace")
        raise RuntimeError(f"configmap patch failed with HTTP {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(f"configmap patch failed: {error.reason}") from error


def main() -> int:
    try:
        data = load_dashboard_config()
        updated_data, failures, success_count = collect_metrics(data)
        nodes_json = json.dumps(updated_data, indent=4)
        patch_configmap(nodes_json)
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    print(f"Collected node metrics for {success_count} node(s)")
    for node in updated_data.get("nodes", []):
        if "temperatureC" in node:
            print(
                f"- {node['name']}: {node['temperatureC']:.1f} C | "
                f"load {node['loadAverage1m']:.2f} | up {node['uptimeHuman']}"
            )

    if failures:
        print("Node metric warnings:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())