# Project Overview

## Summary

This project is a personal Raspberry Pi homelab cluster built to learn Kubernetes, self-hosting, distributed systems, and infrastructure management in a hands-on way.

The cluter is designed to serve two purposes:

1. Act as a practical learning environment for cluster orchestration and homelab tooling
2. Serve as a deployment target for personal applications, including a custom cluster dashboard and a future finance tracker app

## Goals

The main golas of this project are:

- Build and document a functional 4-node Raspberry Pi cluster
- Learn K3s and core Kubernetes concepts in a small-scale environment
- Create a custom dashboard for an external monitor
- Deploy personal applications to the cluster over time
- Build a polished GitHub project that reflects real engineering practices

## Current Scope

The current scope of the project includes:

- Assembling and documenting the physical Raspberry Pi cluster
- Defining node roles and network layout
- Preparing the cluster for K3s
- Building a custom `cluster-dashboard` application
- Documenting the system architecture and setup process

## Planned Stack

### Infrastructure
- Raspberry Pi 5 and Raspberry Pi 4B nodes
- Raspberry Pi OS Lite (64-bit)
- K3s for lightweight Kubernetes
- Wired Ethernet networking through an unmanaged switch

### Applications
- `cluster-dashboard` for monitor-friendly status and service navigator
- `finance-tracker` as a future deployed application

### Tooling
- `uv` for Python package and environment management
- FastAPI for future backend services
- Vanilla HTML, CSS, and JavaScript for the first dashboard version

### Project Philosophy

This project is intentionally being built in small, clear phases. The goal is to keep the system understandable, well-documented, and easy to evolve.

This project prioritizes:
- Simplicity over unnecessary complexity
- Visibility over hidden magic
- Documentation alongside implementation
- Real deployable outcomes over throwaway experimentation

## Near-Term Milestones

- Document hardware, node roles, and network topology
- Build the first version of the cluster dashboard
- Prepare the cluster for K3s installation
- Create a monitor-friendly display workflow
- Establish a clean GitHub project structure and task list