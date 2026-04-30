# Raspberry Pi Homelab Cluster

A 4-node Raspberry Pi cluster for learning Kubernetes, self-hosting applications, and building a production-style personal infrastructure project.

---

## Overview

This project is a hands-on environment for:

- Learning K3s (lightweight Kubernetes)
- Hosting personal applications
- Building a custom dashboard for an external monitor
- Creating a clean, portfolio-quality GitHub project

---

## Hardware

- 2× Raspberry Pi 5  
- 2× Raspberry Pi 4B  
- UCTRONICS 4-layer cluster case  
- NETGEAR GS305 5-port switch  
- 4× 64GB microSD cards  
- USB-C power supplies  
- Portable HDMI monitor  
- Ethernet cabling  

---

## Current State

- 4-node Raspberry Pi cluster (K3s)
- Static dashboard application
- Deployed to Kubernetes (NodePort + GHCR image)
- Dedicated kiosk display node
- Fully automated boot-to-dashboard pipeline

---

## Architecture

```text
[ Laptop ]
    ↓
[ Router ]
    ↓
[ Switch ]
 ├── pi-master (Pi 5)
 ├── pi-worker-1 (Pi 5)
 ├── pi-worker-2 (Pi 4B)
 └── pi-worker-3 (Pi 4B)

External Monitor → cluster-dashboard
```

---

## Structure

```text
infra/
  k3s/
  dashboard/
  monitoring/
  apps/
    cluster-dashboard/   # current focus
    finance-tracker/     # future

docs/
assets/
scripts/  # Python utilities (uv)
```

---

## Stack

- K3s
- `uv` (Python package management)
- GitHub Actions + GitHub Container Registry
- Vanilla HTML/CSS/JS

---

## Status

In progress - cluster operations, dashboard deployment, and documentation

## Dashboard Deployment

The cluster dashboard is built as a static nginx image and published to:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:latest
```

Kubernetes manifests for the app live under:

```text
infra/apps/cluster-dashboard/k8s/
```

Deployment notes and rollout commands live in:

```text
docs/k8s-deployment.md
```

---

## Kiosk Display

The dashboard runs on a dedicated Raspberry Pi using a minimal kiosk setup:

- No desktop environment
- No display manager
- Uses `cage` + `chromium`
- Launches automatically on boot

See [Kiosk Setup](docs/kiosk-setup.md)

---

## Philosophy

- Keep it simple
- Document everything
- Build real, deployable systems