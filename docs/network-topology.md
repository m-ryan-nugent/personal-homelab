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

### Planned IP Address Mapping

| Hostname      | Planned IP Address    | Role    |
|---------------|-----------------------|---------|
| pi-master     | Raspberry Pi 5        | Master  |
| pi-worker-1   | Raspberry Pi 5        | Worker  |
| pi-worker-2   | Raspberry Pi 4B       | Worker  |
| pi-worker-3   | Raspberry Pi 4B       | Worker  |

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