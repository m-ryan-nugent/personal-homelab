# Initial Architecture Diagram

## Overview

This diagram shows the initial logical architecture of the homelab cluster.

It is intentionally simple and represents the current planned system rather than the fully implemented final state.

## Rough Architecture Diagram

```mermaid
flowchart TD
    U[Laptop / Admin Machine] --> R[Home Router]
    R --> S[NETGEAR GS305 Switch]

    S --> M[pi-master<br/>Raspberry Pi 5<br/>K3s Control Plane]
    S --> W1[pi-worker-1<br/>Raspberry Pi 5<br/>Primary Workload Node]
    S --> W2[pi-worker-2<br/>Raspberry Pi 4B<br/>Worker Node]
    S --> W3[pi-worker-3<br/>Raspberry Pi 4B<br/>Worker Node]

    M --> D[cluster-dashboard]
    W1 --> A1[Future Apps]
    W2 --> MON[Monitoring Tools]
    W3 --> EXP[Experiments / Utility Workloads]

    DISP[External HDMI Monitor] --> D
```

## Notes
- `pi-master` is planned as the K3s control plane node.
- Worker nodes will host applications, monitoring tools, and future experiments.
- The custom `cluster-dashboard` is planned as the main user-facing UI for the external monitor.
- Administration will primarily happen from a laptop over SSH and browser-based tools.