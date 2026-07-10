## Why

`TopLevelTracker` reports `available == True` on wlroots compositors but
never actually delivers a single `toplevel` event, so the app-state
registry's open/focused tracking silently does nothing there — the exact
three-state icon behaviour it was built for (greyscale / color / focused)
never activates, and the shell looks stuck in its no-protocol two-state
fallback even on compositors that fully support the protocol.

The cause was mis-diagnosed as a compositor limitation (Wayfire not
emitting toplevels). Empirical testing proved otherwise: the bug is in the
tracker's own event loop. It uses `Display.dispatch(block=True)`, which
does not flush the manager `bind` / handle-creation requests to the
compositor, so the compositor never starts sending events. Using
`Display.roundtrip()` in the loop instead delivers `toplevel`, `app_id`,
and `state` (focus) events correctly — verified live under both Wayfire
0.10.1 and Hyprland 0.55.4.

## What Changes

- Replace the `dispatch(block=True)` loop in `TopLevelTracker._run` with a
  `roundtrip()`-based loop that actually flushes outgoing requests, so
  `toplevel`/`app_id`/`state` events are delivered.
- Add a small idle sleep between roundtrips to avoid a busy-spin, since
  `roundtrip()` returns promptly rather than blocking on the socket.
- Keep the background-thread + `GLib.idle_add` marshalling model
  unchanged; only the inner loop mechanism changes.
- Regression coverage that asserts the tracker's loop uses a
  flushing mechanism, so this cannot silently regress to the
  non-delivering `dispatch` form.

## Capabilities

### New Capabilities
- `wayland-toplevel-tracking`: the guarantee that, on a compositor
  advertising `zwlr_foreign_toplevel_manager_v1`, the tracker delivers
  open/close/focus events to its callbacks (not merely reports the
  protocol available).

### Modified Capabilities
(none — `app-state-registry` already specifies focus behaviour
abstractly; this change makes the underlying delivery actually work and
is not itself a requirement change to that capability, which is not yet
synced to `openspec/specs/`.)

## Impact

- `sugar-next/sugar_next/shell/toplevel_tracker.py` — the `_run` loop.
- No API change: `TopLevelTracker`'s constructor, callbacks, and
  `available` property are unchanged.
- Unblocks the three-state icon rendering delivered by the
  `color-system-and-icon-state` change on every wlroots compositor.
- No new dependencies.
