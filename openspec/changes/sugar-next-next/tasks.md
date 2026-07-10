# Sugar Next Next — Tasks

## 1. Home View layout interface (SUPERSEDED by section 12)

- [x] 1.1 Design `HomeViewLayout` interface
- [x] 1.2 Adapt `shell/app-grid.py` to implement the layout interface
- [x] 1.3 Implement `shell/desktop-grid.py`
- [x] 1.4 Implement `shell/search-first.py`
- [x] 1.5 Wire layout switching at runtime
- [x] 1.6 Smoke test

## 2. Settings panel (partial — layout selector to be removed per section 12)

- [x] 2.1 Write `shell/settings.py`
- [x] 2.2 Add background image picker
- [x] 2.3 Add accent color picker
- [x] 2.4 Add contrast slider
- [x] 2.5 Add icon size control
- [x] 2.6 Add Home View layout selector — **to be removed** (see 12.1)
- [x] 2.7 Add extension manager
- [x] 2.8 Add keybinding viewer and About section

## 3. Color tokens and theming

- [x] 3.1 Define `--sn-bg`, `--sn-bg-alt`, `--sn-accent`, `--sn-text`,
      `--sn-text-secondary`, `--sn-surface` as a base GTK4 CSS stylesheet
- [x] 3.2 Compute tokens from `prefers-color-scheme` at startup
- [x] 3.3 Load `~/.config/sugar-next/colors.css` as a user override
- [x] 3.4 Implement active-app-palette extraction with static-accent fallback
- [x] 3.5 Wire palette tint into Frame and Home View background

## 4. XDG Base Directory and FreeDesktop compliance

- [x] 4.1 Move config reads/writes to `~/.config/sugar-next/`
- [x] 4.2 Confirm all data writes use `~/.local/share/sugar-next/`
- [x] 4.3 Register `org.sugarlabs.SugarNext` D-Bus name
- [x] 4.4 Add MIME type associations for Journal entries
- [x] 4.5 Expose a StatusNotifierItem for background services

## 6. Peer collaboration (exploratory)

- [x] 6.1 Add `on_peer_join`/`on_peer_leave` hooks to `api/hooks.py`
- [ ] 6.2 Research link-local transport — **decided: XMPP**. Needs design
      writeup (transport, library choice, link-local vs. federated).
- [ ] 6.3 Write demo P2P chat extension — UDP prototype done, real XMPP
      extension not started.
- [ ] 6.4 Document collaboration design in `specbook/docs/`
- [ ] 6.5 Smoke test: two instances on same LAN discover each other

## 7. Journal: deeper integration

- [x] 7.1 Add `on_app_close` hook
- [x] 7.2 Update Journal extension to record `kind='close'` entries
- [ ] 7.3 Evaluate Zeitgeist as event source
- [ ] 7.4 Research Nautilus/file manager integration

## 8. Community outreach

- [ ] 8.1 Post to sugar-devel with demo and proposal
- [ ] 8.2 Post to IAEP with educational framing
- [ ] 8.3 Reach out to Walter Bender for feedback

## 9. Extension contract and language backends

- [x] 9.1 Document full extension contract in `specs/extensions/contract.md`
- [ ] 9.2 Implement gjs backend (subprocess, JSON/stdio protocol)
- [ ] 9.3 Implement generic subprocess backend
- [ ] 9.4 Add `on_app_launch` return-value contract (`{"cancel": true}`)
- [ ] 9.5 Document subprocess protocol in `contract.md`
- [ ] 9.6 Write example JS extension (gjs)
- [ ] 9.7 Smoke test: Python, gjs, and subprocess extensions

## 10. Documentation

- [ ] 10.1 Document "Groups" view as future work

## 11. Frame: universal window listing

- [x] 11.1 Add `wlr-foreign-toplevel-management` client via `pywayland`
- [x] 11.2 Wire toplevel events into Frame's running-apps list
- [x] 11.3 Fallback to session-launched apps when protocol unavailable
- [ ] 11.4 Verify against a real Wayfire session

## 12. Views as views — refactor from Settings to Frame navigation

- [ ] 12.1 Remove layout selector from Settings panel
- [ ] 12.2 Add view switcher buttons to Frame overlay bar
      ([Desktop] [Apps] [Search] on the left)
- [ ] 12.3 Wire F1 → Desktop view, F2 → Apps view, F3 → Search view
- [ ] 12.4 Persist active view in config; restore on next launch
- [ ] 12.5 Preserve per-view state across switches
- [ ] 12.6 Remove `HomeViewLayout` interface (no longer needed)
- [ ] 12.7 Smoke test: navigate all views, verify state preservation
