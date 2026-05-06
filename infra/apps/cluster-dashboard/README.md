# Cluster Dashboard

Custom dashboard for my Raspberry Pi homelab cluster.

## Purpose

This application is the monitor-friendly homepage for my homelab. It provides:

- a quick overview of cluster nodes
- a simple list of core services
- a clean UI that can eventually run in kiosk mode on an external display

## Current Phase

Version 1 is intentionally simple:

- frontend: vanilla HTML, CSS, JavaScript
- backend: placeholder only
- data source: static JSON config
- deployment: containerized and published to GitHub Container Registry

## Structure

```text
frontend/
    index.html
    styles.css
    app.js
config/
    nodes.json
backend/
    src/main.py
    pyproject.toml
k8s/
    deployment.yaml
    service.yaml
```

## Features
- Cluster overview header
- Node cards for each Raspberry Pi
- Service cards that distinguish live endpoints from planned services
- Optional per-node `temperatureC`, `loadAverage1m`, and `uptimeHuman` support in the JSON config
- Dark, monitor-friendly styling
- JSON-driven rendering

## Config Notes

The dashboard reads its display data from `config/nodes.json` in local development and from the ConfigMap in Kubernetes.

Service entries can either be live links:

```json
{
    "name": "Cluster Dashboard",
    "url": "http://10.0.0.101:30080/frontend/",
    "status": "Live",
    "description": "Current kiosk dashboard served from K3s"
}
```

or planned entries without a URL yet:

```json
{
    "name": "Grafana",
    "status": "Planned",
    "description": "Monitoring and metrics UI once the stack is deployed"
}
```

When you are ready to surface Raspberry Pi temperatures, add an optional `temperatureC` field to any node:

```json
{
    "name": "pi-worker-1",
    "temperatureC": 48.6
}
```

The node card will show the temperature row automatically when that field is present.

The same pattern works for load average and uptime:

```json
{
    "name": "pi-worker-1",
    "loadAverage1m": 0.42,
    "uptimeHuman": "2d 6h"
}
```

To collect those temperatures from the Pis over SSH and sync them into both the local JSON file and the Kubernetes ConfigMap, run:

```bash
uv run python scripts/src/sync_dashboard_temperatures.py
```

Run that command from a machine that already has key-based SSH access to the Pi nodes. The script uses non-interactive `ssh` and will not prompt for passwords.

Useful options:

```bash
uv run python scripts/src/sync_dashboard_temperatures.py --dry-run
uv run python scripts/src/sync_dashboard_temperatures.py --node pi-worker-1
uv run python scripts/src/sync_dashboard_temperatures.py --ssh-user pi
```

The script tries `vcgencmd measure_temp` first and falls back to `/sys/class/thermal/thermal_zone0/temp` if needed.

After it updates `infra/apps/cluster-dashboard/k8s/configmap-config.yaml`, apply the ConfigMap so the running dashboard picks up the new values:

```bash
kubectl apply -f infra/apps/cluster-dashboard/k8s/configmap-config.yaml
```

The Deployment now mounts the entire `/usr/share/nginx/html/config` directory instead of a `subPath`, so ConfigMap updates can refresh in the running pod without a rollout restart.

If you want the cluster to refresh node metrics automatically, the Kubernetes manifests now include:

- `k8s/temperature-sync-rbac.yaml`
- `k8s/cronjob-temperature-sync.yaml`

That `CronJob` runs from the dedicated `cluster-dashboard-temperature-sync` image, reads the current `nodes.json` from the live dashboard ConfigMap, collects temperature, load average, and uptime over SSH using a mounted key, and patches the ConfigMap in-cluster every 5 minutes.

After you push these repo changes, cut the next release tag before applying the updated `CronJob` manifest so the versioned sync image exists in GHCR.

## Local Development

For local development, the dashboard can be served using a simple HTTP server.

From this directory:

```bash
uv run python -m http.server 8000
```

Then open:

```text
http://localhost:8000/frontend/
```

## Container Image

The production image is built from this directory and published to GitHub Container Registry:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:v1.0.3
```

The automated metric sync job has its own image:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard-temperature-sync:v1.0.3
```

The GitHub Actions workflow lives at:

```text
.github/workflows/build-cluster-dashboard.yml
```

It publishes multi-architecture images for both the dashboard and the metric sync job, plus a `latest` tag from `main`, short SHA tags for debug builds, and version tags for releases.

To prepare the next release tag without hand-editing multiple files, run:

```bash
uv run python scripts/src/release_dashboard.py <version>
```

## Kubernetes Deployment

The dashboard is deployed to K3s using:

- `nginx` as the static web server
- a ConfigMap for `config/nodes.json`
- a Deployment that pulls from GHCR
- a NodePort service on port `30080`

The nginx container serves the dashboard from `/frontend/` and the config JSON from `/config/nodes.json`.

It is accessible at:

```text
http://<node-ip>:30080/frontend/
```

Example:

```text
http://10.0.0.101:30080/frontend/
```

The root URL now redirects to `/frontend/`, but the kiosk can continue using the explicit `/frontend/` path.

This repo's nginx config should return dashboard HTML for that URL. A browser page that shows raw text `404 page not found` means the request is reaching some other server or a stale cluster route.

## Rollout Notes

The earlier node-local image workflow has been removed from the manifests.

The Deployment no longer depends on:

- `nodeSelector` or `nodeName` pinning for `pi-worker-1`
- retagging images directly inside K3s/containerd

The expected rollout flow is now:

1. Push dashboard changes to `main`.
2. Create and push a release tag such as `<version>`.
3. GitHub Actions publishes `ghcr.io/m-ryan-nugent/cluster-dashboard:v1.0.3`.
4. Apply the updated manifest.
5. K3s pulls the image on whichever node schedules the pod.

`latest` is still available for development, but the Deployment should point at an explicit release tag.

The kiosk should continue to load the app at:

```text
http://10.0.0.101:30080/frontend/
```

Useful checks:

```bash
curl -i http://10.0.0.101:30080/frontend/
kubectl get deploy,svc,pods,endpoints -n homelab -o wide
kubectl rollout status deployment/cluster-dashboard -n homelab
kubectl describe pod -n homelab -l app=cluster-dashboard
```

## Kiosk Display

The dashboard is displayed on a dedicated Raspberry Pi node (`pi-worker-1`) using a minimal kiosk setup:

- `cage` (Wayland compositor)
- `chromium` in fullscreen mode
- Automatic launch on boot

The kiosk points to the Kubernetes-hosted dashboard, not a local server.

## Planned Improvements
- Add real-time status data
- Add backend API
- Run in kiosk mode on the external monitor