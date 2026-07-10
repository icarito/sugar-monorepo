#!/usr/bin/env bash
# Run Sugar Next inside a nested Hyprland compositor window.
#
# Why: Hyprland is Sugar Next's target compositor for the standalone
# session. Unlike Wayfire, it is independent (no wlroots), supports
# dynamic tiling, and has a powerful IPC (hyprctl) that Sugar Next can
# consume to integrate its Frame with the compositor's stripe.
#
# This opens a single Hyprland window inside your current Wayland session
# using the Aquamarine Wayland backend. Sugar Next autostarts inside it.
# Close the Hyprland window to end the session.
#
# Hyprland 0.55+ uses Lua for configuration. A minimal config is in
# dev/hyprland.lua alongside this script.

set -euo pipefail

DEV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$DEV_DIR/.." && pwd)"

VENV_PY="${SUGAR_NEXT_PYTHON:-$HOME/.local/share/sugar-next/venv/bin/python3}"
if [ ! -x "$VENV_PY" ]; then
    echo "error: venv python not found at $VENV_PY" >&2
    echo "       set SUGAR_NEXT_PYTHON to override." >&2
    exit 1
fi

if [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "error: no WAYLAND_DISPLAY — run this from inside a Wayland session." >&2
    exit 1
fi

export AQ_BACKENDS=wayland
export SUGAR_NEXT_PROJECT_DIR="$PROJECT_DIR"
export SUGAR_NEXT_PYTHON="$VENV_PY"
export SUGAR_NEXT_NESTED_SIZE="${SUGAR_NEXT_NESTED_SIZE:-1024x640}"
export SUGAR_NEXT_NESTED_SCALE="${SUGAR_NEXT_NESTED_SCALE:-1}"
if [ -z "${SUGAR_NEXT_LAYER_SHELL_PRELOAD:-}" ] &&
        [ -r /usr/lib/liblayer-shell-preload.so ]; then
    export SUGAR_NEXT_LAYER_SHELL_PRELOAD=/usr/lib/liblayer-shell-preload.so
fi
SUGAR_NEXT_DECORATED_HOST="${SUGAR_NEXT_DECORATED_HOST:-0}"

echo "Starting nested Hyprland; Sugar Next will autostart inside it."
echo "Nested output: ${SUGAR_NEXT_NESTED_SIZE}@60 scale ${SUGAR_NEXT_NESTED_SCALE}"
if [ -n "${SUGAR_NEXT_LAYER_SHELL_PRELOAD:-}" ]; then
    echo "Layer-shell preload: ${SUGAR_NEXT_LAYER_SHELL_PRELOAD}"
fi
echo "Close the Hyprland window to exit."

if [ "$SUGAR_NEXT_DECORATED_HOST" = "1" ] &&
        command -v gamescope >/dev/null 2>&1; then
    width="${SUGAR_NEXT_NESTED_SIZE%x*}"
    height="${SUGAR_NEXT_NESTED_SIZE#*x}"
    if [ "$width" != "$SUGAR_NEXT_NESTED_SIZE" ] && [ -n "$height" ]; then
        echo "Host wrapper: gamescope"
        exec gamescope \
            --backend wayland \
            --expose-wayland \
            -W "$width" -H "$height" \
            -w "$width" -h "$height" \
            -r 60 \
            -- Hyprland -c "$DEV_DIR/hyprland.lua"
    fi
fi

exec Hyprland -c "$DEV_DIR/hyprland.lua"
