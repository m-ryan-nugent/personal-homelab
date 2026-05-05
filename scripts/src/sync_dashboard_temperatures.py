from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "infra/apps/cluster-dashboard/config/nodes.json"
CONFIGMAP_PATH = REPO_ROOT / "infra/apps/cluster-dashboard/k8s/configmap-config.yaml"
TEMP_RE = re.compile(r"temp=([0-9]+(?:\.[0-9]+)?)'C")
REMOTE_COMMANDS = (
    "vcgencmd measure_temp",
    "cat /sys/class/thermal/thermal_zone0/temp",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Raspberry Pi temperatures and sync them into the dashboard config."
    )
    parser.add_argument(
        "--ssh-user",
        default="pi",
        help="SSH user for connecting to each node. Defaults to 'pi'.",
    )
    parser.add_argument(
        "--node",
        action="append",
        default=[],
        help="Limit collection to a specific node name. Repeat to target multiple nodes.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="SSH connect timeout in seconds. Defaults to 5.",
    )
    parser.add_argument(
        "--skip-configmap",
        action="store_true",
        help="Only update infra/apps/cluster-dashboard/config/nodes.json.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect temperatures and print a summary without writing files.",
    )
    return parser.parse_args()


def load_dashboard_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def select_nodes(data: dict, requested_names: list[str]) -> list[dict]:
    nodes = data.get("nodes", [])
    if not requested_names:
        return nodes

    available = {node.get("name") for node in nodes}
    missing = [name for name in requested_names if name not in available]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"unknown node names: {names}")

    requested = set(requested_names)
    return [node for node in nodes if node.get("name") in requested]


def parse_temperature_output(output: str) -> float:
    text = output.strip()
    match = TEMP_RE.search(text)
    if match:
        return float(match.group(1))

    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text):
        value = float(text)
        return value / 1000 if value > 1000 else value

    raise ValueError(f"unrecognized temperature output: {text!r}")


def run_remote_command(host: str, ssh_user: str, command: str, timeout: int) -> subprocess.CompletedProcess[str]:
    ssh_command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={timeout}",
        f"{ssh_user}@{host}",
        command,
    ]
    return subprocess.run(
        ssh_command,
        capture_output=True,
        text=True,
        timeout=timeout + 2,
        check=False,
    )


def collect_temperature(node: dict, ssh_user: str, timeout: int) -> float:
    host = node.get("ip")
    if not host:
        raise RuntimeError(f"node {node.get('name', '<unknown>')} is missing an IP address")

    errors: list[str] = []
    for command in REMOTE_COMMANDS:
        try:
            result = run_remote_command(host, ssh_user, command, timeout)
        except subprocess.TimeoutExpired:
            errors.append(f"{command}: command timed out")
            continue

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            errors.append(f"{command}: {message}")
            continue

        try:
            return round(parse_temperature_output(result.stdout), 1)
        except ValueError as error:
            errors.append(f"{command}: {error}")

    node_name = node.get("name", host)
    joined = "; ".join(errors)
    raise RuntimeError(f"{node_name}: {joined}")


def collect_temperatures(data: dict, ssh_user: str, timeout: int, requested_names: list[str]) -> tuple[dict, list[str], int]:
    updated_data = copy.deepcopy(data)
    selected_nodes = select_nodes(updated_data, requested_names)
    failures: list[str] = []
    success_count = 0

    for node in selected_nodes:
        try:
            node["temperatureC"] = collect_temperature(node, ssh_user, timeout)
            success_count += 1
        except RuntimeError as error:
            node.pop("temperatureC", None)
            failures.append(str(error))

    if success_count == 0:
        raise RuntimeError("temperature collection failed for every selected node")

    updated_data["lastUpdated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return updated_data, failures, success_count


def write_dashboard_config(data: dict, dry_run: bool) -> None:
    if dry_run:
        return
    CONFIG_PATH.write_text(json.dumps(data, indent=4) + "\n")


def write_configmap(data: dict, dry_run: bool) -> None:
    if dry_run:
        return

    text = CONFIGMAP_PATH.read_text()
    marker = "data:\n  nodes.json: |\n"
    marker_index = text.find(marker)
    if marker_index == -1:
        raise RuntimeError(f"unable to locate nodes.json block in {CONFIGMAP_PATH}")

    header = text[: marker_index + len(marker)]
    body = json.dumps(data, indent=4)
    indented_body = "\n".join(f"    {line}" for line in body.splitlines())
    CONFIGMAP_PATH.write_text(header + indented_body + "\n")


def main() -> int:
    args = parse_args()

    try:
        data = load_dashboard_config()
        updated_data, failures, success_count = collect_temperatures(
            data,
            ssh_user=args.ssh_user,
            timeout=args.timeout,
            requested_names=args.node,
        )
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1

    write_dashboard_config(updated_data, dry_run=args.dry_run)

    if not args.skip_configmap:
        try:
            write_configmap(updated_data, dry_run=args.dry_run)
        except RuntimeError as error:
            print(error, file=sys.stderr)
            return 1

    scope = ", ".join(args.node) if args.node else "all nodes"
    action = "Dry run complete for" if args.dry_run else "Collected temperatures for"
    print(f"{action} {scope}: {success_count} successful readings")

    for node in updated_data.get("nodes", []):
        if "temperatureC" in node and (not args.node or node.get("name") in args.node):
            print(f"- {node['name']}: {node['temperatureC']:.1f} C")

    if failures:
        print("Temperature collection warnings:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)

    if args.dry_run:
        print("No files were changed.")
    else:
        print(f"Updated {CONFIG_PATH.relative_to(REPO_ROOT)}")
        if args.skip_configmap:
            print("Skipped ConfigMap sync.")
        else:
            print(f"Updated {CONFIGMAP_PATH.relative_to(REPO_ROOT)}")
            print("Apply the ConfigMap to the cluster:")
            print("  kubectl apply -f infra/apps/cluster-dashboard/k8s/configmap-config.yaml")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())