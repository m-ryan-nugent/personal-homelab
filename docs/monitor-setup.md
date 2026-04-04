# Monitor / Kiosk Setup

## Overview

The cluster dashboard is displayed on an external monitor using a dedicated Raspberry Pi node (`pi-worker-1`) running Raspberry Pi OS Desktop.

The system is configured to automatically launch the dashboard in fullscreen kiosk mode on boot.

## Approach

Initial attempts used a `.desktop` autostart file, but this proved unreliable under the LXDE session used by Raspberry Pi OS.

The final solution uses LXDE's native autostart configuration.

## Configuration

File:

`~/.config/lxsession/LXDE-pi/autostart`

Contents:

```text
@xset s off
@xset -dpms
@xset s noblank

@/usr/bin/chromium
--kiosk
--incognito
--noerrdialogs
--disable-infobars
http://localhost:8000/frontend/
```

## Behavior

- System boots
- User auto-logs into desktop
- LXDE session starts
- Chromium launches automatically
- Dashboard loads fullscreen on monitor

## Notes

- `localhost` is used to avoid network dependency
- Dashboard is served via systemd service
- Screen sleep is disabled for continuous display