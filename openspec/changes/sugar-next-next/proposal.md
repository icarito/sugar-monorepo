## Why

`sugar-next` (Fases 1-4) shipped a working GTK4 shell: App Grid, extension
API, Frame, and an opt-in Journal, all installable via `bootstrap.sh`. That
change's proposal success criteria are fully satisfied, and it is being
archived alongside this proposal. The remaining scope sketched in its
`design.md` — a pluggable, user-customizable Home View, exploratory peer
collaboration, deeper Journal integration, and community outreach — was
deferred rather than dropped, so it needs its own change to avoid
re-opening an already-archived proposal.

## What Changes

- Add a pluggable Home View: desktop-grid (Endless-inspired, background +
  floating icons + container folders), app-grid (port of the current
  prototype), and search-first layouts, swappable at runtime and shippable
  as extensions.
- Add a Settings panel: background image picker, accent color picker,
  contrast slider, icon size preference, Home View layout selector,
  extension manager, keybinding viewer.
- Implement the `--sn-*` color token system from `sugar-next/HIG.md`:
  tokens set from `prefers-color-scheme`, user override via
  `~/.config/sugar-next/colors.css` or the Settings panel, and the active
  app's palette subtly tinting shell chrome (Frame, Home View background).
- Adopt XDG Base Directory compliance for config/data
  (`~/.config/sugar-next/`, `~/.local/share/sugar-next/`), plus the
  remaining FreeDesktop citizenship items from the HIG's compliance list:
  `org.sugarlabs.SugarNext` D-Bus name, MIME type associations for Journal
  entries, and StatusNotifierItem (system tray) for background services.
- Support school-locked layouts via config file (deployment-time policy,
  not a runtime toggle exposed to learners).
- Add exploratory peer collaboration: `on_peer_join`/`on_peer_leave` hooks
  in the extension API, a demo link-local P2P chat extension, and a
  written comparison of XMPP link-local vs. WebRTC vs. custom UDP as
  transport options — research only, no committed transport in this
  change.
- Extend the Journal extension: `on_app_close` hook, evaluation of
  Zeitgeist as an event source, and research into Nautilus/file-manager
  integration.
- Community outreach: post to sugar-devel and IAEP with a demo, and reach
  out to Walter Bender for feedback.
- Document (not implement) the "Groups" view from the four-views model —
  activities as named, sharable temporal contexts spanning multiple apps —
  as explicit future work gated on the extension API proving itself
  first, per the HIG's own framing.

## Capabilities

### New Capabilities
- `home-view`: pluggable Home View layouts (desktop-grid, app-grid,
  search-first) and the Settings panel that configures them.
- `peer-collaboration`: presence hooks and demo P2P extension for
  link-local peer discovery and chat (exploratory).

### Modified Capabilities
- (none — no existing `openspec/specs/` capability covers Sugar Next yet;
  this change introduces the first ones)

## Impact

- Affected code: `sugar-next/shell/` (new `home-view.py`, `settings.py`,
  layout widgets), `sugar-next/api/hooks.py` (new hooks), `sugar-next/data/`
  (default config), `examples/extensions/journal.py`.
- New dependency surface (research only, not adopted yet): XMPP client
  library (e.g. slixmpp) or WebRTC/UDP alternative — decision deferred to
  design.md and this change's own follow-up if a transport is selected.
- No changes to the `sugar` (jarabe) repo or other Sugar Labs repos.
