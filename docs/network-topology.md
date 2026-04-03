 Network Topology

## Overview

The homelab cluster uses a simple wired network topology.

Each Raspberry Pi connects by Ethernet to a central unmanaged switch. The switch then connects upstream to the local router. This setup provides a stable network foundation for cluster communication and future service hosting.

## Physical Topology

```text
[ Router ]
    |
    | 3 ft Ethernet
    |
[ NETGEAR GS305 Switch ]
    |------ pi-master
    |------ pi-worker-1
    |------ pi-worker-2
    |------ pi-worker-3
```

## Planned Network Design

The cluster will use static IP addresses so that nodes can be reached consistently over SSH, K3s, and future internal services.

## IP Address Mapping

The cluster uses static IP addresses within the local `10.0.0.x` subnet.

| Hostname      | IP Address   | Role    |
|---------------|-------------|---------|
| pi-master     | 10.0.0.100  | Master  |
| pi-worker-1   | 10.0.0.101  | Worker  |
| pi-worker-2   | 10.0.0.102  | Worker  |
| pi-worker-3   | 10.0.0.103  | Worker  |

Gateway: `10.0.0.1`  
Subnet: `10.0.0.0/24`

## Why Wired Networking

Wired Ethernet is being used instead of Wi-Fi because it offers:

- Lower latency
- Better reliability
- More predictable cluster communication
- Easier troubleshooting

This is especially important for Kubernetes, service discovery, and node-to-node communication.

## Monitor Usage

The external HDMI monitor is not part of the network topology itself, but it will be used to display the custom cluster dashboard in a monitor-friendly kiosk-style view.

## Future Networking Considerations

Possible future improvements include:
- Tailscale for secure remote access
- DNS or local hostname resolution improvements
- Internal ingress routing for services
- Service exposure through a reverse proxy

## Implementation Notes

### Network Configuration Approach

Initial attempts to assign static IPs using `/etc/dhcpcd.conf` were unsuccessful because the system was using NetworkManager for network configuration.

Static IPs were ultimately configured using `nmcli` on the `netplan-eth0` connection.

Example:

```bash
nmcli con mod netplan-eth0 \
  ipv4.addresses 10.0.0.100/24 \
  ipv4.gateway 10.0.0.1 \
  ipv4.dns 10.0.0.1 \
  ipv4.method manual
```

### Key Lessons
- Raspberry Pi OS may use NetworkManager instead of `dhcpcd`
- Configuration tools must match the active network manager
- Incorrect subnet assumptions (e.g., `192.168.x.x` vs `10.0.0.x`) can break connectivity
- Bringing interfaces down will temporarily drop SSH connections (expected behavior)

### Recovery Strategies Used
- Reconnecting via `.local` hostname
- Checking router for DHCP-assigned IPs
- Rebooting nodes to reapply configuration