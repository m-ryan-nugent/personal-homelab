# Monitor / Kiosk Setup

## Current Setup

The dashboard is displayed on an external monitor connected to `pi-worker-1`.

The current setup no longer uses LXDE autostart or a local systemd HTTP server. The dashboard is served from K3s and opened directly by Chromium in kiosk mode at boot.

The authoritative setup is documented in [kiosk-setup.md](kiosk-setup.md).

## Active Launch Path

```text
systemd
	-> getty (tty1)
		-> autologin (pi user)
			-> bash (~/.bash_profile)
				-> cage
					-> chromium
						-> http://10.0.0.101:30080/frontend/
```

Relevant Chromium target:

```text
http://10.0.0.101:30080/frontend/
```

## Legacy Note

An earlier prototype used Raspberry Pi OS Desktop, LXDE autostart, and a local dashboard served from `http://localhost:8000/frontend/`.

That setup is obsolete after moving the dashboard into K3s and should not be used as the monitor boot target.

## Troubleshooting

If the monitor shows raw text `404 page not found`, the request is not reaching the nginx container defined in this repo.

Check these first:

- Verify the kiosk startup command still points to `http://10.0.0.101:30080/frontend/`
- Confirm the NodePort responds with dashboard HTML rather than plain-text 404
- Confirm the `cluster-dashboard` Service, Pod, and Endpoints exist in namespace `homelab`

Quick verification from a cluster node:

```bash
curl -i http://10.0.0.101:30080/frontend/
kubectl get svc,pods,endpoints -n homelab
```

## Known Dashboard Failure Path

The dashboard issue traced through two separate layers:

1. The kiosk boot target in `~/.bash_profile` was briefly pointing at the NodePort root instead of `/frontend/`, which explained the plain-text 404 on the monitor.
2. Once the Chromium target was corrected, K3s was confirmed to be serving the app, but the `cluster-dashboard` Deployment was in a partially broken rollout.

The working dashboard traffic was still being handled by an older healthy pod on `pi-worker-1` using a local image, while Kubernetes was trying and failing to start a newer `cluster-dashboard:v3` pod on `pi-worker-3` where that image did not exist.

Operational takeaway:

- Keep the kiosk pointed at `http://10.0.0.101:30080/frontend/`
- Verify rollout health with `kubectl get deploy,rs,pods -n homelab -o wide`
- Treat the image on `pi-worker-1` as `docker.io/library/cluster-dashboard:local` when inspecting or retagging it in containerd
- Pin the dashboard Deployment to `pi-worker-1` when using the locally tagged `v3` image there