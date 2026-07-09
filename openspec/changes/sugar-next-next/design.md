## Context

`sugar-next`'s archived `design.md` already sketched this scope (Home View
layouts, Settings, collaboration, deeper Journal) as forward-looking
sections written before Fases 1-4 were implemented. This design carries
those sections forward, adjusted for what Fases 1-4 actually built:

- The App Grid (`shell/app-grid.py`) exists and works — it becomes one of
  three Home View layouts, not a rewrite.
- The extension API (`api/hooks.py`) has `on_app_launch` and
  `on_shell_start`. `on_peer_join`/`on_peer_leave`/`on_app_close` are new.
- Frame v0 (per the archived design's "v0 scope note") shows pinned
  favorites + session-launched apps only — no `wlr-foreign-toplevel-management`
  yet. Settings' "keybinding viewer" and layout selector don't depend on
  that gap, so they're unaffected.
- The Journal extension (`examples/extensions/journal.py`) writes to
  `~/.local/share/sugar-next/journal.sqlite` with `entries(id, timestamp,
  app_id, title, kind)`. `on_app_close` support means adding a
  `kind='close'` row, not a schema change.
- `sugar-next/HIG.md` (written by the design agent alongside Fases 1-4 but
  not yet implemented) specifies concrete pieces this change must also
  cover: the `--sn-*` color token system with a user override file
  (`~/.config/sugar-next/colors.css`), active-app-palette tinting of shell
  chrome, an icon-size Settings control, and the remaining FreeDesktop
  compliance items (D-Bus name, MIME associations, StatusNotifierItem).
  These are folded into this change rather than the collaboration-only
  scope originally sketched in `sugar-next`'s archived `design.md`.

## Goals / Non-Goals

**Goals:**
- Ship a pluggable Home View with three layouts and a Settings panel to
  switch between them, matching the archived design's sketch. The Learner
  always has full control of this choice — no deployment-level override.
- Land XDG Base Directory compliance so config and data are where other
  Linux tooling expects them.
- Add presence hooks and a demo P2P chat extension as an exploratory,
  optional feature — not a committed collaboration platform.
- Improve the Journal extension incrementally (`on_app_close`, Zeitgeist
  evaluation) without a backend rewrite.
- Get outside feedback (sugar-devel, IAEP, Walter Bender) before investing
  further in collaboration or Home View polish.

**Non-Goals:**
- Choosing and shipping a production collaboration transport (XMPP,
  WebRTC, or UDP). This change only researches and demos link-local chat.
- Full `wlr-foreign-toplevel-management` window listing for Frame — still
  future work per the archived design.
- Migrating the Journal off SQLite or onto Zeitgeist as its primary store
  — evaluation only.
- Redesigning the App Grid's existing behavior; it's ported into the
  Home View layout interface as-is.

## Decisions

**Home View as a layout interface, not a rewrite.** Define a common
widget interface (e.g. a `HomeViewLayout` base with `on_activate`,
`on_deactivate`, and a `Gtk.Widget` root) that `app-grid.py` is adapted to
implement, alongside new `desktop-grid.py` and `search-first.py` modules.
Alternative considered: three independent, unrelated shell modes selected
at launch time — rejected because it would prevent runtime switching from
Settings, which the proposal requires.

**Collaboration: hooks and a demo, XMPP research deferred.** Add
`on_peer_join`/`on_peer_leave` to `api/hooks.py` now, since they're cheap
and stable regardless of transport. Build the demo chat extension on
link-local discovery (Avahi/DNS-SD) with the simplest transport that
proves the hook shape — deferring the XMPP-vs-WebRTC-vs-UDP choice to a
short written comparison rather than an implementation. Rationale: the
archived design already flagged collaboration as "a design direction, not
a committed feature," and picking a transport before there's a second
real extension using it risks over-building.

**Color tokens as CSS custom properties, loaded via GTK4's CSS provider.**
Define `--sn-bg`, `--sn-bg-alt`, `--sn-accent`, `--sn-text`,
`--sn-text-secondary`, `--sn-surface` in a base stylesheet computed from
`prefers-color-scheme` at startup. Load
`~/.config/sugar-next/colors.css` after the base sheet if present, so user
overrides win via normal CSS cascade — no custom override-merging logic
needed. Active-app-palette tinting reads the focused window's
`Gio.AppInfo` icon, extracts a dominant color (simple average, not a full
palette-extraction library), and sets `--sn-accent` dynamically; falls
back to the static accent color when extraction is inconclusive (e.g.
monochrome icons). Alternative considered: a Python theming object with
getters — rejected because CSS custom properties are already GTK4-native
and the Settings panel can write directly to the override file instead of
maintaining a separate serialization format.

**Icon size as a Settings slider affecting Home View layouts uniformly.**
Store as a single scale factor (e.g. small/medium/large or a numeric
multiplier) applied by whichever Home View layout is active, not a
per-layout setting — keeps Settings simple and matches the HIG's framing
of it as one Home View preference alongside background and accent.

**XDG compliance items done as small, independent additions.** The
D-Bus name, MIME associations, and StatusNotifierItem are unrelated to
each other and to Home View/collaboration work, so each is a standalone
task gated only on whether it's needed for the shell to behave well as a
desktop citizen — not blocking or blocked by the rest of this change.

**Journal: additive changes only.** Add `on_app_close` to the hook
scanner and have the existing Journal extension subscribe to it,
appending `kind='close'` rows to the current schema. Zeitgeist and
Nautilus integration are written up as research findings (feasibility,
API surface, effort estimate), not implemented, since neither is required
for the Journal to keep working.

## Risks / Trade-offs

- **Home View layout interface adds indirection to a shell that's still
  small.** → Keep the interface to the minimum needed (activate/
  deactivate/root widget); don't generalize further until a third
  consumer (an extension-provided layout) actually needs it.
- **Collaboration demo could imply more commitment than intended.** →
  Label the chat extension and its docs "exploratory" and keep it out of
  the default extension set; it ships in `examples/extensions/`, same
  pattern as the Journal's opt-in install.
- **Community outreach (C.1-C.3) has no engineering rollback.** → Treat as
  a task with a real dependency on Fases above being demo-able; sequence
  it last in tasks.md.
- **`on_app_close` PID watching relies on a GLib fallback, not a real
  parent-child relationship.** Discovered during implementation:
  `Gio.AppInfo.launch()` commonly reparents the launched process to the
  user's systemd instance (transient scope/portal activation) rather than
  forking it as our direct child. `GLib.child_watch_add()` still fires
  because it falls back to polling `/proc` when `waitpid()` reports
  ECHILD — reliable on Linux (Sugar Next's only target) but not the
  textbook-correct mechanism. → Accepted for v0; a fully correct version
  would track the systemd transient scope via `org.freedesktop.systemd1`
  and its `JobRemoved` signal, deferred as unnecessary complexity unless
  it proves flaky in practice.
- **`on_app_close` never fires at all for `DBusActivatable` apps** (e.g.
  Nautilus, GNOME Connections). Discovered during manual testing: these
  apps are launched via a D-Bus `Activate` call, not `fork+exec`, and
  `Gio.AppLaunchContext`'s `"launched"` signal reports `pid=0` for them —
  not a real process to watch. `desktop_bundle.py`'s `_on_launched` now
  skips close-tracking when `pid` is falsy, which stops the app from
  getting stuck in the Frame forever (the original bug), but does **not**
  make the icon disappear when the learner closes the window — under the
  `on_app_close` fallback path there is no way to detect that without
  real window tracking. → Only `wlr-foreign-toplevel-management` (section
  10; unverified on a real Wayfire session, see 10.4) can fix this
  properly, since it tracks windows, not processes. Documented as a known
  gap of the fallback path, not silently masked.

## Migration Plan

No data migration: Journal schema is additive, and XDG Base Directory
paths (`~/.local/share/sugar-next/`, `~/.config/sugar-next/`) match what
`sugar-next` already used for its data directory — only formalizing
config placement is new. No rollback concerns beyond normal git revert.

## Open Questions

- Which link-local transport does the demo chat extension actually use
  (Avahi service discovery + what payload channel)? To be resolved during
  Fase 6 research, documented before Fase 6 implementation tasks start.
- Does Zeitgeist evaluation conclude "adopt," "defer," or "reject"? Drives
  whether Fase 7's Journal work continues past this change or becomes its
  own follow-up.
