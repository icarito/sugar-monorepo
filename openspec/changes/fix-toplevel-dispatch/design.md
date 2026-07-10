## Context

`TopLevelTracker._run` (in `toplevel_tracker.py`) runs the Wayland event
loop on a daemon thread and marshals results to the GTK thread via
`GLib.idle_add`. Its current inner loop is:

```python
manager.dispatcher["toplevel"] = self._on_toplevel_created
while self._running:
    self._display.dispatch(block=True)
```

`Display.dispatch(block=True)` reads and dispatches incoming events but
does **not** flush the client's outgoing request buffer. The manager
`bind` (issued during the initial `roundtrip`) and, more importantly, the
per-handle `NewId` bookkeeping that the protocol expects are never
flushed to the compositor, so the compositor does not begin streaming
`toplevel` events. The result: `available` is `True` (the bind proxy
exists locally) but no event ever arrives.

This was empirically isolated. Under both Wayfire 0.10.1 (wlroots-0.19.3)
and Hyprland 0.55.4, a probe using `roundtrip()` in the loop received
`toplevel`, `app_id`, and `state` (with `activated == True` for the
focused window); the same probe using `dispatch(block=True)` — even with
an added `flush()` before the loop, and even with `flush()` before each
`dispatch()` — received nothing.

## Goals / Non-Goals

**Goals:**
- Make the tracker actually deliver open/close/focus events on wlroots
  compositors, using a mechanism proven to work.
- Preserve the existing threading and `GLib.idle_add` marshalling model.
- Add a regression guard so the loop cannot revert to a non-delivering
  form unnoticed.

**Non-Goals:**
- Switching to the `ext_foreign_toplevel_list_v1` protocol. It is the
  modern standard and pywayland ships a binding, but it only *enumerates*
  toplevels — it carries no focus/`activated` state — so it cannot
  replace `zwlr_foreign_toplevel_manager_v1` for the three-state icon
  feature. Considered and rejected here; may be added later as a fallback
  enumerator.
- Any compositor migration (Hyprland adoption is a separate exploration).
- Changing the tracker's public surface.

## Decisions

**Use `roundtrip()` in the loop, not `dispatch()` + `flush()`.**
Testing showed a single `flush()` after registration, and a `flush()`
before each `dispatch(block=True)`, both still delivered zero events —
only `roundtrip()` worked. `roundtrip()` flushes the outgoing buffer,
then blocks for the server to process and reply, which is what actually
kicks the compositor into streaming toplevel events. It is heavier than a
bare dispatch, but this loop runs on its own thread and toplevel churn is
low-frequency (windows opening/closing/focusing), so the cost is
irrelevant here.

New inner loop shape:

```python
manager.dispatcher["toplevel"] = self._on_toplevel_created
while self._running:
    self._display.roundtrip()
    time.sleep(self._POLL_INTERVAL)   # e.g. 0.1s
```

**Add a small sleep between roundtrips.**
Unlike `dispatch(block=True)`, `roundtrip()` returns as soon as the
server replies rather than blocking until the next event, so a bare
`while` loop would busy-spin a core. A ~100 ms sleep bounds focus/open
latency to a fraction of a second (imperceptible for icon state) while
keeping the thread idle between events. The interval is a named constant
so it is easy to tune.

**Stop must still interrupt promptly.**
`stop()` sets `self._running = False` and disconnects the display. With
the sleep at ~100 ms, the loop exits within one interval. `roundtrip()`
on a disconnected display raises, which is already caught by the
surrounding `try/except`, so teardown stays clean.

**Regression guard by asserting the loop mechanism.**
A pure unit test cannot spin up a compositor, and the repo's dev machine
runs GNOME (no protocol at all). So the guard asserts, by source
inspection or by a seam, that `_run` uses `roundtrip` and not a bare
`dispatch(block=True)` loop — cheap insurance against a well-meaning
refactor silently reintroducing the exact bug this change fixes.

## Risks / Trade-offs

- [`roundtrip()` blocks the tracker thread until the server round-trips;
  a wedged compositor could stall the loop] → It is a daemon thread with
  no GTK work on it, and `stop()` disconnects the display to break out;
  the shell's main loop is unaffected.
- [The ~100 ms poll adds latency to focus/open reflection] → Imperceptible
  for icon saturation state; tunable via the named constant if a future
  use wants tighter timing.
- [Source-inspection regression guard is coarser than a behavioural test]
  → Accepted: a behavioural test needs a live wlroots compositor the CI
  environment does not have. The guard specifically prevents reverting to
  the known-broken form, which is the concrete failure mode.

## Open Questions

- Whether to later add `ext_foreign_toplevel_list_v1` as a
  focus-less enumeration fallback for compositors that expose only the
  `ext_` protocol and not the `zwlr_` one. Out of scope here; noted for a
  future change.
