#!/usr/bin/env bash
# Records a scripted Sugar Next demo to an mp4, with zero manual input.
#
# Method: force GDK_BACKEND=x11 so the GTK4 window gets a real X11 window
# (visible to xwininfo/ffmpeg) even under a Wayland session via XWayland;
# launch demo_driver.py, which drives the shell through a canned sequence
# of view switches / pin-unpin / Frame / Settings via GLib timeouts (no
# xdotool needed); grab that window's contents with `ffmpeg -f x11grab`
# for the driver's lifetime, then stop when it exits on its own.
#
# This intentionally bypasses the Wayland screencast portal's interactive
# consent dialog (x11grab captures the X11 window directly, no portal
# involved) — only run this with the user's explicit go-ahead for the
# current session; don't invoke it unattended.
#
# Usage:
#   ./record.sh [output.mp4]
#
# Requires: ffmpeg, xwininfo (both already present on this workspace's
# dev machine). Does not require xdotool or wf-recorder.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HOME/sugar-next-demo-$(date +%Y-%m-%d-%H%M%S).mp4}"

echo "Starting Sugar Next (X11 backend) with the demo driver..."

# Clean state so the demo always starts from Desktop view with no
# favorites pinned, matching the scripted narration in demo_driver.py.
rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/sugar-next/settings.json"
rm -f "${XDG_DATA_HOME:-$HOME/.local/share}/sugar-next/favorites.json"

GDK_BACKEND=x11 python3 "$SKILL_DIR/demo_driver.py" &
DRIVER_PID=$!

# Give the window time to map before we go looking for it.
sleep 1.5

WIN_ID=""
for _ in $(seq 1 20); do
  WIN_ID=$(xwininfo -root -tree 2>/dev/null \
    | grep '"Sugar Next' \
    | grep -v 'mutter-x11-frames' \
    | head -1 \
    | awk '{print $1}')
  if [ -n "$WIN_ID" ]; then
    break
  fi
  sleep 0.3
done

if [ -z "$WIN_ID" ]; then
  echo "Could not find the Sugar Next window; is the demo driver running under X11?" >&2
  kill "$DRIVER_PID" 2>/dev/null || true
  exit 1
fi

echo "Recording window $WIN_ID to $OUT"

# -f x11grab captures the window contents directly. The driver process
# exits on its own once its scripted sequence finishes, which is the
# signal to stop recording.
ffmpeg -y -f x11grab -window_id "$WIN_ID" -framerate 15 -i :0 \
  -c:v libx264 -pix_fmt yuv420p -crf 20 \
  "$OUT" &
FFMPEG_PID=$!

wait "$DRIVER_PID"
echo "Demo driver finished; stopping recording."
kill -INT "$FFMPEG_PID" 2>/dev/null || true
wait "$FFMPEG_PID" 2>/dev/null || true

echo "Saved: $OUT"
