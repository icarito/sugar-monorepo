# Proposal: sugar-next-session-host

## Why

Sugar Next currently runs as a regular Wayland client — one window among
many on whatever compositor happens to host it. This works for development
but prevents it from being a real shell. A shell owns the session: it
controls window placement, tiling, focus, and the running-apps list. The
current approach requires fragile workarounds (`zwlr_foreign_toplevel`
client, pid-watch `/proc` polling) just to observe what's open, and even
then cannot manage or tile windows.

Instead of growing more workarounds, Sugar Next should target being the
session owner with Hyprland as its compositor base. Hyprland offers dynamic
tiling, powerful IPC (`hyprctl`), `zwlr_foreign_toplevel_manager_v1` with
full focus/activated state, and an extensible config system (Lua since
0.55). Sugar Next's Frame can consume Hyprland IPC to show running
activities, and the stripe/bar can be configured to complement rather than
conflict with the Frame.

## What Changes

- Add `dev/run-hyprland-nested.sh` and `dev/hyprland.lua` for iterative
  development in a nested Hyprland window (using `AQ_BACKENDS=wayland`),
  equivalent to the existing `dev/run-wayfire.sh` for Wayfire.
- Integrate the Frame with Hyprland's IPC: read window list, workspaces,
  and focus state from `hyprctl clients`, `hyprctl activewindow`, and
  `hyprctl workspaces` JSON output, replacing or augmenting the current
  `TopLevelTracker` as the source of truth.
- Design and document the standalone session entry: a
  `/usr/share/wayland-sessions/sugar-next.desktop` that launches Hyprland
  with Sugar Next as the session shell (autostart via `hl.exec_cmd()` from
  the `hyprland.start` event in `hyprland.lua`).
- Define the Frame ↔ Hyprland stripe contract: what Hyprland bar/workspace
  widgets Sugar Next consumes vs. what the Frame renders itself, so the
  two don't duplicate or fight.
- Keep the existing `TopLevelTracker` as a development fallback inside
  GNOME/Mutter (where Hyprland is not running) but make Hyprland IPC the
  primary path when `HYPRLAND_INSTANCE_SIGNATURE` is set.
- Initialize Sugar Next as a GTK layer-shell surface when
  `Gtk4LayerShell`/`GtkLayerShell` GI bindings are available, with the
  fullscreen xdg-toplevel rule kept as the fallback.
- Document the tiling layout policy for activities: dwindle by default,
  fullscreen for activity focused mode, escape hatch for apps that need
  floating.

## Capabilities

### New Capabilities

- `session-hosting`: Sugar Next owns the Wayland session atop Hyprland —
  launches apps into a tiling layout, tracks them via Hyprland IPC, and
  surfaces them in the Frame. The standalone session entry and `exec-once`
  autostart contract are part of this spec.
- `frame-compositor-integration`: the Frame's running list and focus state
  are sourced from Hyprland's IPC rather than from a separate toplevel-
  tracking client, and the Frame complements (does not replace) the
  Hyprland stripe/bar.

### Modified Capabilities

- `wayland-toplevel-tracking`: demoted from the primary tracking mechanism
  to a dev-only fallback when running under a non-Hyprland compositor.

## Impact

- **Code**: `sugar_next/shell/main.py` (Hyprland IPC integration),
  `sugar_next/shell/hyprland_ipc.py` (new module), `sugar_next/shell/frame.py`
  (IPC-sourced running list), `sugar_next/shell/toplevel_tracker.py`
  (conditional: Hyprland present → skip).
- **Config**: `dev/hyprland.lua` (minimal dev config with autostart),
  `dev/run-hyprland-nested.sh` (dev runner script).
- **Session**: new `sugar-next.desktop` in `/usr/share/wayland-sessions/`
  for standalone login (packaging concern, documented here).
- **Dependencies**: Hyprland 0.55+ with `hyprctl` on PATH.
  No new Python dependencies.
- **Behavior**: when `HYPRLAND_INSTANCE_SIGNATURE` is set, Sugar Next skips
  the `TopLevelTracker` and reads window state directly from Hyprland IPC.
  This is zero-config — no user toggle needed.
