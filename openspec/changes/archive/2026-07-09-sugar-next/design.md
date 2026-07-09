# Sugar Next — Design

*for **A Learning Shell for Everyday Computing***

## Architecture

```
sugar-next/
├── shell/                  # GTK4 shell (replaces jarabe)
│   ├── main.py             # Entry point
│   ├── home-view.py        # Configurable Home View (desktop/grid/search)
│   ├── app-grid.py         # App grid widget
│   ├── frame.py            # Universal frame
│   ├── settings.py         # Settings panel
│   └── extensions/         # Extension loader
├── bundles/                # Bundle types
│   ├── activity-bundle.py  # Sugar activity wrapper
│   └── desktop-bundle.py   # .desktop file wrapper
├── api/                    # Extension API
│   └── hooks.py            # on_app_launch, etc.
├── data/                   # Default config, icons
└── pyproject.toml          # pip-installable package
```

## Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Shell | GTK4 + Python (PyGObject) | Community already has GTK4 experience from toolkit-gtk4 |
| Extension API | Python, no GObject needed | Low floor for creators |
| App scanner | XDG Desktop Menu spec | Zero-config, works with any Linux distro |
| Packaging | pip + OCI | Self-contained, any distro; no Nix dependency |
| Compositor | Wayland (host compositor) | No embedded compositor needed — Sugar Next runs as a normal Wayland client |
| Home View | Pluggable layouts (desktop grid, app grid, search-first) | End-user chooseable; schools can lock a layout |
| Collaboration | XMPP hooks (exploratory) | Presence hooks in extension API; demo chat as first step |

## Home View (pluggable)

The Home View is the learner's primary workspace. Three built-in layouts:

1. **Desktop grid** (Endless-inspired) — icons float on a user-selectable
   background image. Supports container folders that expand into sub-grids
   with pagination. Default for full-shell mode.

2. **App Grid** (current prototype) — `Gtk.FlowBox` with search bar, no
   background image visible behind icons. Default for windowed mode.

3. **Search-first** — blank canvas with a search bar at top. No icons
   visible until the learner types. Minimal distraction, full focus.

Layouts are widgets that implement a common interface, swappable at
runtime. Additional layouts can be shipped as extensions.

## The four views (reimagined)

Sugar's classic four-view navigation recontextualized for modern hardware:

| View | Key | Description |
|------|-----|-------------|
| Focus | — | Fullscreen app window (any app, not just "activities") |
| Home | F6 | The configurable Home View (desktop grid, app grid, or search) |
| Groups | F7 | Named, sharable contexts — a "project" spanning multiple apps and people |
| Neighborhood | F8 | Peer discovery: link-local + federated presence |

F6/F7/F8 are default bindings, configurable in Settings.

## App Grid (Fase 1)

- Simple `Gtk.FlowBox` with category sections
- Icons from `.desktop` files (via `Gio.DesktopAppInfo`)
- Click → `Gio.AppInfo.launch()`
- Search bar at the top
- Container folders: category clusters that expand into sub-grids
- Future: favorite/star system, activity overlay

## Extension API (Fase 2)

```python
# ~/.local/share/sugar-next/extensions/my-ext.py

def on_app_launch(app_id: str, app_info: Gio.AppInfo) -> None:
    """Called before an app launches."""
    print(f"Launched {app_id}")

def on_shell_start() -> None:
    """Called when the shell starts."""
    pass

def on_peer_join(peer_id: str, peer_name: str) -> None:
    """Called when a peer is discovered on the LAN."""
    pass

def on_peer_leave(peer_id: str) -> None:
    """Called when a peer disconnects."""
    pass
```

Minimal, synchronous hooks. No GObject, no decorators, no registration step.

## Frame (Fase 3+)

- Shows all windows (not just Sugar activities)
- Accessed via hot-corner or keybinding (F6)
- Per-window palette: "Pin to favorites", "Add to Journal", etc.
- Icons mode first, thumbnails later

**v0 scope note** (decided during implementation): as a normal Wayland
client, the shell cannot enumerate other clients' windows — that needs the
`wlr-foreign-toplevel-management` protocol, which GTK does not expose and
which would add a pywayland dependency and compositor coupling. Frame v0
therefore shows **pinned favorites + apps launched this session** (hot
corner + F6, per-item palette). True universal window listing is future
work.

## Design system

- **Light/dark**: respects `prefers-color-scheme`, with user override.
- **High contrast**: shell provides a contrast slider independent of theme.
- **Active app tint**: the shell chrome subtly shifts to echo the focused
  application's icon palette — the learner always knows where their
  attention is without looking away from the content.
- **Tokens**: CSS custom properties (`--sn-bg`, `--sn-accent`, etc.),
  documented in `sugar-next/HIG.md`.
- **Background image**: user-selectable, stretches or tiles.
- **Accent color**: user-pickable from presets or custom hex.

## Settings

A minimal Settings panel accessible from the Frame:

- Background image picker
- Accent color picker
- Contrast slider
- Home View layout selector
- Extension manager (list, enable, disable)
- Keybinding viewer
- About

## XDG FreeDesktop compliance

- `.desktop` file installed by `bootstrap.sh` (done)
- XDG Desktop Menu spec for app scanning (done)
- XDG Base Directory spec (`~/.local/share/sugar-next/`, `~/.config/sugar-next/`)
- `org.sugarlabs.SugarNext` D-Bus name (future)
- `wlr-foreign-toplevel-management` protocol for window listing (future)
- MIME type associations for Journal entries (future)
- StatusNotifierItem (system tray) for background services (future)

## Activity model (reimagined)

An "Activity" in Sugar Next is not a bundle type. It is a **temporal
context**: a named, sharable workspace that can span multiple apps.
Example: a learner researching birds has a browser tab, a terminal, and a
drawing app open. They name this context "Birds". Sugar Next tracks which
apps belong to it, can share the whole context with a peer, and records it
in the Journal as a single episode.

This is future work — the extension API must first prove itself. But the
principle is set: activities are not apps, they are agglomerations of apps
in time.

## Collaboration (exploratory)

Collaboration is a design direction, not a committed feature. The first
concrete step is presence hooks in the extension API (`on_peer_join`,
`on_peer_leave`) and a demo P2P chat extension. Full XMPP infrastructure
(link-local + federated) is documented as a reference for future research
on what is pragmatic to deliver.

```
Presence bus (XMPP) — exploratory design
├── link-local: zero-config LAN discovery (Avahi/DNS-SD), no account
├── federated: standard XMPP server for cross-network presence
└── Share substrate exposed via extension API:
    ├── cursor/share
    ├── clipboard exchange
    └── app-level data channels (extensions opt in)
```

The presence bus would be a shell service — it must be active for any peer
discovery. The share substrate is an API that apps call through extensions,
never coupling them to XMPP directly.

## Journal (Fase 4, opt-in)

- Not part of the shell by default
- Extension that subscribes to `on_app_launch` and `on_app_close`
- Explicit publish: user chooses what goes into the Journal
- Backend: SQLite flat file, no D-Bus service

**v0 API** (decided during implementation): the Journal ships as a regular
extension file (`examples/extensions/journal.py`) — installing it *is* the
opt-in. It subscribes to `on_app_launch` and records events into
`~/.local/share/sugar-next/journal.sqlite`, one table:

```sql
CREATE TABLE entries (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,   -- ISO 8601
    app_id TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL         -- 'launch' for now; 'close', 'publish' later
);
```

A promising richer event source is **Zeitgeist** (the freedesktop activity
log): instead of the shell tracking everything itself, the Journal
extension could subscribe to Zeitgeist events (documents opened, apps
closed) and keep SQLite only as its publish store. Integrating with
**Nautilus** or other file managers for Journal-aware file browsing is
also a research direction.
