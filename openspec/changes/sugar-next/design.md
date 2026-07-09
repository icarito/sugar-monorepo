# Sugar Next — Design

## Architecture

```
sugar-next/
├── shell/                  # GTK4 shell (replaces jarabe)
│   ├── main.py             # Entry point
│   ├── app-grid.py         # App grid view
│   ├── frame.py            # Universal frame (future)
│   └── extensions/         # Extension loader
├── bundles/                # Bundle types
│   ├── activity-bundle.py  # Sugar activity wrapper
│   └── desktop-bundle.py   # .desktop file wrapper
├── api/                    # Extension API
│   └── hooks.py            # on_app_launch, etc.
├── data/                   # Default config, icons
└── nix/                    # Nix flake for self-contained build
```

## Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Shell | GTK4 + Python (PyGObject) | Community already has GTK4 experience from toolkit-gtk4 |
| Extension API | Python, no GObject needed | Low floor for creators |
| App scanner | XDG Desktop Menu spec | Zero-config, works with any Linux distro |
| Packaging | Nix flake + OCI | Self-contained, any distro |
| Compositor | Wayland (host compositor) | No embedded compositor needed — Sugar Next runs as a normal Wayland client |

## App Grid (Fase 1)

- Simple `Gtk.FlowBox` with category sections
- Icons from `.desktop` files (via `Gio.DesktopAppInfo`)
- Click → `Gio.AppInfo.launch()`
- Search bar at the top
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
```

Minimal, synchronous hooks. No GObject, no decorators, no registration step.

## Frame (Fase 3+)

- Shows all windows (not just Sugar activities)
- Accessed via hot-corner or keybinding
- Per-window palette: "Pin to favorites", "Add to Journal", etc.
- Icons mode first, thumbnails later

## Journal (Fase 4, opt-in)

- Not part of the shell by default
- Extension that subscribes to `on_app_launch` and `on_app_close`
- Explicit publish: user chooses what goes into the Journal
- Backend: SQLite flat file, no D-Bus service
