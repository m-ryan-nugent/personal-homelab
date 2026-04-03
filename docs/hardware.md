# Hardware Inventory

## Overview

This document lists the physical hardware currently allocated to the Raspberry Pi homelab cluster.

## Core Hardware

### Cluster Chassis
- **UCTRONICS Raspberry Pi Cluster Case**
- 4-layer desktop metal rack case
- Includes 2 cooling fans
- Compatible with Raspberry Pi 5 / 4B and 2.5" SSD form factors

### Network Switch
- **NETGEAR GS305**
- 5-port Gigabit Ethernet unmanaged switch

### Power Supplies
- **4x CanaKit 45W USB-C Power Supply**

### Display
- **LOLG Portable Monitor**
- HDMI connection
- Planned use: external dashboard display / kiosk-style monitor

## Compute Nodes

### Node 1
- Raspberry Pi 5

### Node 2
- Raspberry Pi 5

### Node 3
- Raspberry Pi 4B

### Node 4
- Raspberry Pi 4B

## Storage

### Boot Media
- **4x 64GB microSD cards**

## Cabling

### Ethernet
- **4x 6-inch Ethernet cables**
  - intended for Raspberry Pi to switch connections inside or near the rack
- **1x 3-foot Ethernet cable**
  - intended for switch to router/uplink connection

## Notes

- The cluster uses mixed Raspberry Pi hardware:
  - 2 Raspberry Pi 5 nodes
  - 2 Raspberry Pi 4B nodes
- This makes the cluster heterogeneous, which is acceptable for learning and for lightweight workloads.
- The Raspberry Pi 5 nodes are better suited for the control plane and higher-priority workloads.
- The portable monitor will be used primarily for the custom cluster dashboard rather than direct administration.