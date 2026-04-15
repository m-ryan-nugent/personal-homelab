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

### Remove keyring prompts

```bash
sudo apt purge -y gnome-keyring libpam-gnome-keyring
```

## Key Decisions

- Avoided full desktop environment (LXDE)
- Avoided display manager (LightDM)
- Used `cage` for minimal, single-app display
- Used `localhost`/NodePort for stable dashboard access

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
