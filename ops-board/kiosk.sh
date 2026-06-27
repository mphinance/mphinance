#!/usr/bin/env bash
# TraderDaddy Pro Ops Board — Raspberry Pi kiosk launcher
# For Raspberry Pi OS Lite (manual path). FullPageOS users: skip this, see README.
#
# Install once:
#   sudo apt update && sudo apt install -y --no-install-recommends \
#       xserver-xorg xinit chromium-browser unclutter x11-xserver-utils
#   chmod +x kiosk.sh
#   echo "@reboot xinit /home/pi/ops-board/kiosk.sh -- :0" >> /etc/xdg/lxsession/...  # or use the systemd unit in README
#
# Appliance default: the Pi serves the board to itself on localhost (see README).
# Override with OPS_URL to point at Venus, a LAN host, or a public URL.

URL="${OPS_URL:-http://localhost:8077/}"

# Keep the screen awake forever — no blanking, no DPMS, no screensaver.
xset s off
xset -dpms
xset s noblank

# Hide the cursor after 0.1s idle.
unclutter -idle 0.1 -root &

# Chromium kiosk. Flags tuned for a Pi 3 (low memory, no crash bubbles, GPU on).
exec chromium-browser \
  --kiosk "$URL" \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --disable-features=Translate \
  --check-for-update-interval=31536000 \
  --autoplay-policy=no-user-gesture-required \
  --incognito \
  --disable-pinch \
  --overscroll-history-navigation=0
