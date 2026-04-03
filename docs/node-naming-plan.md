# Node Naming Plan

## Purpose

This document defines the naming convention and intended roles for each Raspberry Pi node in the homelab cluster.

A consistent naming plan makes the cluster easier to manage, document, and expand later.

## Naming Convention

The cluster uses a simple role-based naming convention:

- `pi-master`
- `pi-worker-1`
- `pi-worker-2`
- `pi-worker-3`

This convention is easy to remember, easy to reference in documentation, and aligns well with the initial K3s cluster design.

## Node Assignments

| Hostname      | Device Model     | Role    | Intended Purpose              |
|---------------|------------------|---------|-------------------------------|
| pi-master     | Raspberry Pi 5   | Master  | K3s control plane             |
| pi-worker-1   | Raspberry Pi 5   | Worker  | Primary workload node         |
| pi-worker-2   | Raspberry Pi 4B  | Worker  | Secondary workload node       |
| pi-worker-3   | Raspberry Pi 4B  | Worker  | Secondary workload node       |

## Role Definitions

### Master Node
The master node is responsible for:
- hosting the K3s control plane
- coordinating the cluster
- serving as the primary management node

### Worker Nodes
The worker nodes are responsible for:
- running deployed workloads
- hosting applications and services
- supporting cluster experiments and monitoring tools

## Future Naming Considerations

If the cluster grows later, the same naming pattern can continue:

- `pi-worker-4`
- `pi-worker-5`

If additional special-purpose nodes are introduced, a more descriptive naming pattern could be adopted, such as:

- `pi-storage-1`
- `pi-monitor-1`
- `pi-gpu-1`

For now, the simple master/worker naming scheme is the best fit for the project.