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
- deployment: local development first, Kubernetes later

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
- Service cards for key tools and apps
- Dark, monitor-friendly styling
- JSON-driven rendering

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

## Kubernetes Deployment (Current Setup)

The dashboard is deployed to the K3s cluster using:
- `nginx` (container)
- ConfigMaps for static files
- NodePort service

The nginx container serves the dashboard from `/frontend/` and the config JSON from `/config/nodes.json`.

It is accessible at:

```text
http://<node-ip>:30080/frontend/
```

Example:

```text
http://10.0.0.101:30080/frontend/
```

This repo's nginx config should return dashboard HTML for that URL. A browser page that shows raw text `404 page not found` means the request is reaching some other server or a stale cluster route.

## Rollout Notes

The kiosk must load the app at `/frontend/`:

```text
http://10.0.0.101:30080/frontend/
```

Pointing Chromium at the NodePort root instead of `/frontend/` produces a plain-text 404 even when the Service itself is reachable.

An April 2026 incident exposed an additional Kubernetes-specific failure mode:

- The NodePort service, pod, and endpoint were healthy enough to serve the dashboard.
- The visible dashboard traffic was still coming from an older healthy pod on `pi-worker-1`.
- At the same time, the Deployment was trying and failing to roll out a newer `cluster-dashboard:v3` pod on `pi-worker-3` because the local image was missing there.

When inspecting images directly in K3s/containerd on `pi-worker-1`, the working image was stored as:

```text
docker.io/library/cluster-dashboard:local
```

The recovery path was:

```bash
sudo k3s ctr -n k8s.io images tag \
    docker.io/library/cluster-dashboard:local \
    docker.io/library/cluster-dashboard:v3
```

After tagging, keep the Deployment aligned with that node-local image:

- use `docker.io/library/cluster-dashboard:v3` as the image reference
- pin the Deployment to `pi-worker-1` so the kiosk node runs the dashboard pod with the known-good local image

If the Deployment continues to use node-local images, frontend or nginx changes are not picked up automatically by the cluster. Rebuild or retag the image in K3s/containerd on the target node before restarting the deployment.

Useful checks:

```bash
curl -i http://10.0.0.101:30080/frontend/
kubectl get svc,pods,endpoints -n homelab
kubectl get deploy,rs,pods -n homelab -o wide
sudo k3s ctr -n k8s.io images ls | grep cluster-dashboard
```

## Kiosk Display

The dashboard is displayed on a dedicated Raspberry Pi node (`pi-worker-1`) using a minimal kiosk setup:

- `cage` (Wayland compositor)
- `chromium` in fullscreen mode
- Automatic launch on boot

The kiosk points to the Kubernetes-hosted dashboard, not a local server.

## Planned Improvements
- Replace placeholder service links
- Add real-time status data
- Add backend API
- Deploy to K3s
- Run in kiosk mode on the external monitor