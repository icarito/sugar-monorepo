# Sugar Next

A modern, self-contained shell for Sugar Labs: GTK4 + Python, runs as a
normal Wayland client on any current Linux distro. Sugar Next is **not a
fork** of the Sugar shell (jarabe) — it is a sibling project that coexists
with the legacy stack.

- **Activities and system apps coexist** — the App Grid shows everything
  your system knows about (XDG `.desktop` entries), not just XO bundles.
- **Low floor for creators** — a working extension is ~5 lines of plain
  Python. No GObject, no D-Bus, no build system.
  See [the extension API docs](../specbook/docs/sugar-next-extensions.md).
- **Opt-in layers** — Journal, favorites, everything beyond the grid is
  an extension you choose to install.

## Install

```sh
./bootstrap.sh        # pip install --user + desktop entry
sugar-next
```

Requires GTK4 + PyGObject from your distro (`python3-gobject gtk4` on
Fedora, `python3-gi gir1.2-gtk-4.0` on Debian/Ubuntu, `python-gobject gtk4`
on Arch).

Or containerized:

```sh
podman build -t sugar-next -f Containerfile .
podman run --rm \
  -e WAYLAND_DISPLAY -e XDG_RUNTIME_DIR \
  -v "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" \
  --userns=keep-id \
  sugar-next
```

## Using the shell

- **App Grid** — type in the search bar to filter; click an icon to launch.
- **Frame** — press **F6** or hit the top-right hot corner. Shows pinned
  favorites and apps launched this session. Right-click a grid icon to
  "Pin to Frame favorites"; right-click a frame icon for its palette.

## Extensions

Drop a `.py` file in `~/.local/share/sugar-next/extensions/`:

```python
def on_app_launch(app_id, app_info):
    print(f"launching {app_id}")
```

Working examples in [examples/extensions/](examples/extensions/):
`logger.py`, `launch-counter.py`, and `journal.py` (the opt-in Journal,
SQLite-backed).

## Layout

```
sugar_next/
├── shell/          # main.py (app), app_grid.py, frame.py
├── bundles/        # desktop_bundle.py — .desktop wrapper
└── api/            # hooks.py — extension scanner + dispatcher
examples/extensions/
Containerfile
bootstrap.sh
```

## Status

Early prototype driven by the `sugar-next` OpenSpec change in the
SugarLabs workspace repo (see `openspec/changes/sugar-next/`).
