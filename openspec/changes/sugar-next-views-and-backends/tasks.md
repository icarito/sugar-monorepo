# Sugar Next — Views & Extension Backends — Tasks

## 1. Extension contract and language backends

- [x] 1.1 Document the full extension contract in `extension-contract.md`
      (hooks, error isolation, enable/disable, language backends)
- [ ] 1.2 Implement gjs backend (subprocess, JSON/stdio protocol)
- [ ] 1.3 Implement generic subprocess backend
- [ ] 1.4 Add `on_app_launch` return-value contract (`{"cancel": true}`)
- [ ] 1.5 Document the subprocess protocol in `extension-contract.md`
- [ ] 1.6 Write an example JS extension (gjs)
- [ ] 1.7 Smoke test: Python, gjs, and subprocess extensions

## 2. Views as views — refactor from Settings to Frame navigation

Supersedes the Settings-based layout selector shipped by `sugar-next-next`
(its sections 1–2 and the polish pass). The three layouts become
Frame-navigated views, not Settings-selected layouts.

- [ ] 2.1 Remove the layout selector from the Settings panel
- [ ] 2.2 Add view switcher buttons to the Frame overlay bar
      ([Desktop] [Apps] [Search] on the left)
- [ ] 2.3 Wire F1 → Desktop view, F2 → Apps view, F3 → Search view
- [ ] 2.4 Persist the active view in config; restore on next launch
- [ ] 2.5 Preserve per-view state (scroll, search text) across switches
- [ ] 2.6 Retire the `HomeViewLayout` interface (no longer needed)
- [ ] 2.7 Smoke test: navigate all views, verify state preservation
