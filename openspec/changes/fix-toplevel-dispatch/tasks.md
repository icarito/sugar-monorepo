## 1. Fix the event loop

- [ ] 1.1 In `toplevel_tracker.py`, replace the
      `while self._running: self._display.dispatch(block=True)` loop with
      a `roundtrip()`-based loop that flushes outgoing requests each
      iteration
- [ ] 1.2 Add a named poll-interval constant (~0.1s) and a
      `time.sleep(self._POLL_INTERVAL)` between roundtrips to avoid a
      busy-spin; import `time`
- [ ] 1.3 Confirm `stop()` still breaks the loop within one interval and
      that the roundtrip-on-disconnected-display error stays caught by
      the existing `try/except`

## 2. Regression guard

- [ ] 2.1 Add a test asserting the tracker loop uses a flushing mechanism
      (`roundtrip`) and not a bare `dispatch(block=True)` loop — via
      source inspection of `_run` or an equivalent seam — so the exact
      non-delivering form cannot silently return
- [ ] 2.2 Keep/extend existing `test_toplevel_tracker.py` coverage for
      the no-protocol path (`available is False`, callbacks never fire)
      so the fix does not disturb the GNOME fallback

## 3. Live verification (wlroots compositor)

- [ ] 3.1 Under nested Wayfire (`dev/run-wayfire.sh`), launch an app and
      confirm the tracker's open callback fires with the app id
- [ ] 3.2 Confirm the focus callback fires with `activated` when focus
      changes between two open windows
- [ ] 3.3 Confirm pie-menu and app-grid icons now traverse
      greyscale → color → focused (the three-state rendering unblocked by
      this fix)
- [ ] 3.4 Run the full `sugar-next/tests` suite and confirm no regression
