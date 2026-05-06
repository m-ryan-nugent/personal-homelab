# Monitor / Kiosk Setup

## Current Setup

The dashboard is displayed on an external monitor connected to `pi-worker-1`.

The current setup no longer uses LXDE autostart or a local systemd HTTP server. The dashboard is served from K3s and opened directly by Chromium in kiosk mode at boot.

The authoritative setup is documented in [kiosk-setup.md](kiosk-setup.md).

The dashboard container image is now published through GitHub Container Registry and pulled by the cluster at rollout time rather than relying on a node-local image.

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

The NodePort root now redirects to `/frontend/`, but the kiosk should continue to use the explicit `/frontend/` URL.

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

## Operational Notes

Keep the kiosk pointed at `http://10.0.0.101:30080/frontend/`.

For current operations:

- apply updated manifests after a new release instead of relying on node-local images
- verify rollout health with `kubectl get deploy,rs,pods -n homelab -o wide`
- use [k8s-deployment.md](k8s-deployment.md) for the current registry-backed deployment and automated node metric sync procedure