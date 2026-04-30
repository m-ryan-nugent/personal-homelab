# Kiosk / Monitor Setup

## Overview

The cluster dashboard is displayed on a dedicated Raspberry Pi node using a minimal kiosk setup.

Instead of relying on a full desktop environment (LXDE), the system uses:

- `getty` autologin
- `cage` (Wayland compositor)
- `chromium` (fullscreen app)

This results in a lightweight, deterministic startup path with minimal dependencies.

---

## Final Architecture

```text
systemd
  → getty (tty1)
    → autologin (pi user)
      → bash (~/.bash_profile)
        → cage
          → chromium (kiosk)
            → dashboard (K3s)
```

## Configuration

### Enable console autologin

```bash
sudo raspi-config
# System Options → Boot / Auto Login → Console Autologin
```

### Launch cage + Chromium

#### `~/.bash_profile`:

```bash
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec cage chromium \
    --kiosk \
    --incognito \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --force-device-scale-factor=1.25 \
    --window-size=1536,864 \
    http://10.0.0.101:30080/frontend/
fi
```

The kiosk should point at the K3s NodePort URL above, not a local `localhost` dashboard.

The explicit `/frontend/` suffix is still the preferred kiosk target. The dashboard nginx config now redirects the NodePort root to `/frontend/`, but keeping Chromium pointed at the full path avoids ambiguity and keeps the kiosk aligned with the app's real entrypoint.

### Remove keyring prompts

```bash
sudo apt purge -y gnome-keyring libpam-gnome-keyring
```

## Key Decisions

- Avoided full desktop environment (LXDE)
- Avoided display manager (LightDM)
- Used `cage` for minimal, single-app display
- Used a NodePort URL for stable dashboard access

## Issues Encountered

### Broken apt state

- Conflict between `raspberry-ui-mods` and `pi-greeter`
- Fixed with:

```bash
sudo dpkg --configure -a
```

### LightDM session failure

- Invalid session (`rpd-labwc`)
- Fixed by updating to `LXDE-pi-labwc`

### Cage failing over SSH

- Caused by lack of logind seat
- Resolved by running only via tty autologin

### Chromium binary mismatch

- Debian Trixie uses `chromium`, not `chromium-browser`

## Result

The system boots directly into a fullscreen dashboard with:
- No desktop environment
- No login prompts
- No keyring interruptions
- Minimal dependencies

## Troubleshooting

If Chromium shows raw text `404 page not found`, that request is not being served by the dashboard nginx config in this repo.

Verify:

- `~/.bash_profile` still points to `http://10.0.0.101:30080/frontend/`
- `curl -i http://10.0.0.101:30080/frontend/` returns dashboard HTML
- `curl -i http://10.0.0.101:30080/` returns an HTTP redirect to `/frontend/`
- `kubectl get svc,pods,endpoints -n homelab` shows a live `cluster-dashboard` backend

If those checks pass but a rollout is still failing, inspect the Deployment state more closely:

```bash
kubectl get deploy,rs,pods -n homelab -o wide
kubectl describe deployment cluster-dashboard -n homelab
kubectl describe pod -n homelab <failing-pod>
```

## Known Rollout Failure (April 2026)

This section is historical context for the pre-GHCR deployment flow.

One traced failure path looked like this:

- The kiosk boot command had been launching the NodePort root URL instead of `/frontend/`, which produced the original 404 on the monitor.
- After fixing the boot URL, the dashboard was confirmed to be served through K3s by checking the `cluster-dashboard` NodePort Service, Pod, and Endpoints from `pi-master`.
- The Deployment itself was in a partial rollout: the live dashboard was still coming from an older healthy pod on `pi-worker-1`, while Kubernetes was also trying to start a newer `cluster-dashboard:v3` pod on `pi-worker-3`.
- That new pod failed because the image was only present locally on `pi-worker-1` and was missing on `pi-worker-3`.

That failure mode should no longer be the default operating model. The current manifests pull `ghcr.io/m-ryan-nugent/cluster-dashboard:latest` with `imagePullPolicy: IfNotPresent` and do not pin the pod to `pi-worker-1`.

Current rollout expectation:

- push dashboard changes to GitHub
- let GitHub Actions publish the GHCR image
- restart the Deployment when you want the cluster to pull the newest image
- keep the kiosk URL fixed at `http://10.0.0.101:30080/frontend/`

Important detail for K3s/containerd:

- The working image on `pi-worker-1` appeared as `docker.io/library/cluster-dashboard:local`, not just `cluster-dashboard:local`.
- To reuse that image for the rollout, tag it on `pi-worker-1` as `docker.io/library/cluster-dashboard:v3`.
- The Deployment should then be pinned to `pi-worker-1` so the kiosk node keeps running the dashboard pod that has the local image.

Useful node-side check:

```bash
sudo k3s ctr -n k8s.io images ls | grep cluster-dashboard
```

For the current registry-backed flow, prefer these checks instead:

```bash
kubectl rollout restart deployment/cluster-dashboard -n homelab
kubectl rollout status deployment/cluster-dashboard -n homelab
kubectl get pods -n homelab -o wide
```
