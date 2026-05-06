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

## Operational Checks

For the current registry-backed flow, prefer these checks:

```bash
kubectl apply -f infra/apps/cluster-dashboard/k8s/deployment.yaml
kubectl rollout status deployment/cluster-dashboard -n homelab
kubectl get pods -n homelab -o wide
```

Keep the kiosk URL fixed at `http://10.0.0.101:30080/frontend/`. If the dashboard looks stale after a release, check rollout state first, then verify the current ConfigMap if you are also using the automated node metric sync.
