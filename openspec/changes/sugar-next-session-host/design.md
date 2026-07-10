# Design: sugar-next-session-host

## Context

Sugar Next is a `Gtk.Application` (one window) that today launches apps as
sibling windows on the host compositor. It observes them indirectly through
a `zwlr_foreign_toplevel_manager_v1` client (`toplevel_tracker.py`) that
works on wlroots compositors but not on GNOME/Mutter.

Hyprland (0.55.4 installed) is a dynamic tiling Wayland compositor with:
- Independent codebase (not wlroots-based, uses Aquamarine)
- `zwlr_foreign_toplevel_manager_v1` (already verified working in Sugar Next
  tests — open/close/focus events with `activated` state)
- Powerful socket-based IPC (`hyprctl` CLI, `/tmp/hypr/...` socket)
- Lua config since 0.55
- Nested window mode via `AQ_BACKENDS=wayland`

The insight: Sugar Next + Hyprland is a session, not a widget-in-widget
embedding. Sugar Next doesn't need to be a compositor itself — it needs to
be the session shell that talks to its compositor.

## Goals / Non-Goals

**Goals:**
- Develop and test Sugar Next inside a nested Hyprland window (parity with
  the existing Wayfire dev runner).
- Replace `TopLevelTracker` with Hyprland IPC when `HYPRLAND_INSTANCE_
  SIGNATURE` is set — one code path that works everywhere Hyprland runs.
- Define the Frame ↔ stripe contract so the two don't conflict.
- Document the standalone session entry point.

**Non-Goals:**
- Embedding a compositor inside Sugar Next (Casilda — explored, rejected as
  over-engineered for the actual goal).
- Replacing Hyprland's tiling or bar with Sugar Next equivalents.
- Multi-seat, XWayland compatibility (Hyprland handles both natively).
- Migrating classic Sugar activities.

## Decisions

### D1. Hyprland IPC over toplevel tracker when available

When `HYPRLAND_INSTANCE_SIGNATURE` is set, Sugar Next reads window state
from `hyprctl clients -j`, `hyprctl activewindow -j`, and `hyprctl
workspaces -j` instead of running the `TopLevelTracker` thread. The IPC is
synchronous socket-based — low latency, no polling thread needed.

- *Fallback*: when the env var is absent (GNOME, Wayfire, Sway), the
  existing `TopLevelTracker` path remains unchanged.
- *Polling*: `GLib.timeout_add` at ~500ms reads Hyprland state on the GTK
  main thread (JSON parsing is cheap). Hyprland's IPC socket has no push
  notifications, so polling is the standard approach.

### D2. Frame reads Hyprland clients, not a private list

The Frame's running list is derived from `hyprctl clients -j` (all mapped
windows). Each client has `class` (app_id), `title`, `workspace`, and
`focusHistoryID`. The `activewindow` response gives the focused client.
Sugar Next's `app_state` registry stays — it's fed from Hyprland IPC
instead of `TopLevelTracker` callbacks.

### D3. Stripe coexistence: Frame handles app launching + activity switching

The Hyprland bar/stripe shows workspaces and window titles natively. Sugar
Next's Frame handles:
- App launching (grid, pie menu) → spawns apps into Hyprland
- Activity switching via workspace or focus — the Frame "bring to front"
  action issues `hyprctl dispatch focuswindow`
- Running list = Hyprland clients filtered to Sugar-launched app_ids

The bar/stripe is Hyprland's concern; Sugar Next does not inject widgets
into it. Instead, the Frame is a floating overlay (as today) that reads
Hyprland state and dispatches actions.

### D4. Nested dev environment via AQ_BACKENDS=wayland

Hyprland's Aquamarine library supports a Wayland backend for running
Hyprland as a window inside another compositor. The `AQ_BACKENDS=wayland`
env var enables this. One limitation: it creates a virtual output
(`HEADLESS-1`) that needs explicit monitor configuration.

### D5. Standalone session entry

A `/usr/share/wayland-sessions/sugar-next.desktop` file with `Exec=Hyprland
-c /etc/sugar-next/hyprland.lua` (or per-user `~/.config/sugar-next/`) is
the login manager entry. The config file autostarts the Sugar Next shell
with `hl.on("hyprland.start", function() hl.exec_cmd("sugar-next") end)`.
This is documented but not packaged in this change.

### D6. Layer-shell when available, fullscreen toplevel fallback otherwise

Sugar Next's real shell surface should not be a compositor-managed
`xdg_toplevel`. At startup, the shell attempts to load a GTK layer-shell GI
namespace (`Gtk4LayerShell`, falling back to `GtkLayerShell`) and, when
available, initializes the main window as a background layer surface
anchored to all monitor edges. If the binding is absent or incompatible,
startup continues unchanged as an `xdg_toplevel`; the Hyprland window rule
then fullscreen-matches `org.sugarlabs.SugarNext` as the development
fallback.

## Risks / Trade-offs

- [Hyprland IPC polling adds ~500ms latency] → Acceptable for frame updates;
  focus changes are sub-second via `activewindow`. Tighter polling is CPU-
  cheap (socket reads are fast) and tunable.
- [Hyprland is a moving target — config format changed from hyprlang to Lua
  in 0.55] → we target 0.55+ Lua config. The IPC JSON format is more stable.
- [Nested window mode may have quirks] → the `AQ_BACKENDS=wayland` path is
  tested; input forwarding works. If it breaks, Wayfire remains the
  fallback dev compositor.
- [No Casilda means no per-app compositor isolation] → That's the point.
  Hyprland's tiling *is* the window management. Each activity is a Hyprland
  client like any other.

## Migration Plan

1. Land the Hyprland IPC module as opt-in (env var gated). Existing
   `TopLevelTracker` stays.
2. Add dev runner script and config.
3. Once IPC path is stable, make it the default when
   `HYPRLAND_INSTANCE_SIGNATURE` is detected. `TopLevelTracker` is not
   deleted — it remains the GNOME/Wayfire fallback.
4. Document standalone session entry. Packaging is a separate change.

## Open Questions

- Should `hyprctl` polling live on a background thread (like
  `TopLevelTracker` does) or on the GTK main loop via `GLib.timeout_add`?
  Start with main-loop polling (simpler, avoids threading); move to
  background thread if profiling shows UI jank.
- Workspace integration: should Sugar Next launch each activity into its
  own Hyprland workspace, or use a single workspace with tiling? Start with
  single workspace + dwindle tiling; workspace-per-activity can come later.
