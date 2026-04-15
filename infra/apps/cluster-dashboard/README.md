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

It is accessible at:

```text
http://<node-ip>:30080/frontend/
```

Example:

```text
http://10.0.0.101:30080/frontend/
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