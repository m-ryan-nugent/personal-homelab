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

## Container Image

The production image is built from this directory and published to GitHub Container Registry:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:latest
```

The GitHub Actions workflow lives at:

```text
.github/workflows/build-cluster-dashboard.yml
```

It publishes a multi-architecture image for Raspberry Pi nodes and also adds a commit-based SHA tag for rollback/debugging.

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
- `imagePullPolicy: Never`
- retagging images directly inside K3s/containerd

The expected rollout flow is now:

1. Push dashboard changes to `main`.
2. GitHub Actions publishes `ghcr.io/m-ryan-nugent/cluster-dashboard:latest`.
3. Apply manifests or restart the Deployment.
4. K3s pulls the image on whichever node schedules the pod.

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
- Replace placeholder service links
- Add real-time status data
- Add backend API
- Run in kiosk mode on the external monitor