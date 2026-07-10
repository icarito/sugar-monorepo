# Sugar Next — Views & Extension Backends — Tasks

## 1. Extension contract and language backends

- [x] 1.1 Document the full extension contract in `extension-contract.md`
      (hooks, error isolation, enable/disable, language backends)
- [x] 1.2 Implement gjs backend (subprocess, JSON/stdio protocol) —
      `api/backends.py` routes `*.js` to `gjs <file>`.
- [x] 1.3 Implement generic subprocess backend — any executable file is
      run directly; `hooks.py` `_load_backends` wires it in.
- [x] 1.4 Add `on_app_launch` return-value contract (`{"cancel": true}`) —
      `registry.call` now returns results; `call_is_cancelled` +
      `DesktopBundle.launch` honour the veto.
- [x] 1.5 Document the subprocess protocol in `extension-contract.md`
- [x] 1.6 Write an example JS extension (gjs) —
      `examples/extensions/logger.js`
- [x] 1.7 Smoke test: Python, gjs, and subprocess extensions —
      `tests/test_backends.py` (gjs test skips if gjs is absent)

## 2. Views as views — refactor from Settings to Frame navigation

Supersedes the Settings-based layout selector shipped by `sugar-next-next`
(its sections 1–2 and the polish pass). The three layouts become
Frame-navigated views, not Settings-selected layouts.

- [x] 2.1 Remove the layout selector from the Settings panel — gone from
      the Behavior tab; `_on_layout_changed` handler deleted. Settings is
      also no longer modal (confusing as a blocking dialog in a shell).
- [x] 2.2 Add view switcher buttons to the Frame overlay bar
      ([Desktop] [Apps] [Search] on the left) — `Frame.set_view_switcher`
- [x] 2.3 Wire F1 → Desktop view, F2 → Apps view, F3 → Search view —
      `main.py` `_VIEW_KEYS` / `_activate_view` (F10 keeps Settings)
- [x] 2.4 Persist the active view in config; restore on next launch —
      stored under `home_view_layout`; Desktop is the first-run default
- [x] 2.5 Preserve per-view state (scroll, search text) across switches —
      views no longer reset in `on_deactivate`
- [x] 2.6 Retire the `HomeViewLayout` interface (no longer needed) —
      `HomeView` now duck-types views by a `view_id` attribute; the base
      class/mixin is gone, and the vocabulary is `view` throughout
- [x] 2.7 Smoke test: navigate all views, verify state preservation —
      `tests/test_home_view.py` (state preserved), `tests/test_frame.py`
      (view switcher), plus direct F1/F2/F3 + persistence verification
