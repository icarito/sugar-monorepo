# Sugar Next

A modern, self-contained shell in the spirit of Sugar: GTK4 + Python,
running as a normal Wayland client on any current Linux distribution.

**Sugar Next is not a fork and not a replacement.** It is a sibling
project that coexists with the legacy Sugar stack and leaves it untouched.

▶ [20-second demo video](docs/demo.mp4)

## Why

Sugar's founding insight was the **low floor**: a child could look inside
their computer and change it. Twenty years on, the stack that carried that
idea has quietly raised the floor out of reach:

- **GTK3 + X11** — both deprecated upstream. The GTK4 port of the shell
  (sugar PR #1019) stalled on environment friction, not on technical
  difficulty: nobody could easily *run* what they were porting.
- **Autotools** — a build system most of today's contributors have never
  seen.
- **The activities-only bubble** — the shell only shows XO-style bundles.
  Firefox, the terminal, GIMP: invisible. The user is isolated from their
  own computer.
- **A high barrier for creators** — writing a Sugar activity means
  learning GObject Introspection, the activity lifecycle, D-Bus, and the
  build system before printing "hello".
- **No reproducible dev environment** — the recommended setup is a 1 GB
  Live ISO tied to a specific distro version.

The community is active — the energy exists. Sugar Next is a place to
point some of it at *evolving* the environment instead of only
maintaining it.

### Design principles

1. **Activities and system apps coexist.** The App Grid shows everything
   the system knows about (XDG `.desktop` entries). No isolation bubble.
2. **Low floor for creators.** An extension is a plain `.py` file in a
   folder — ~5 lines, no GObject, no D-Bus, no build system, no
   registration. The Journal itself is written this way.
3. **Self-contained and self-hosted.** `pip install` on any distro, or a
   single OCI container. Setup friction is treated as a bug — it is the
   documented reason the last porting effort stalled.
4. **Opt-in, not imposed.** Journal, favorites, collaboration — every
   layer beyond the grid is an extension you choose to install.

### What Sugar Next deliberately does not do

- Touch the `sugar` repo, jarabe, or PR #1019 — the legacy shell stays
  exactly as it is.
- Migrate existing XO activities to a new API (a compat layer may come
  later).
- Reimplement legacy mesh collaboration.

## Install

### Option 1: bootstrap script (recommended)

Requires GTK4 and PyGObject from your distro (pip cannot build PyGObject
without the GObject headers):

| Distro | Command |
|--------|---------|
| Fedora | `sudo dnf install python3-gobject gtk4` |
| Debian/Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0` |
| Arch | `sudo pacman -S python-gobject gtk4` |

Then:

```sh
git clone https://github.com/icarito/sugar-monorepo.git
cd sugar-monorepo/sugar-next
./bootstrap.sh        # pip install --user + desktop menu entry
sugar-next
```

`bootstrap.sh` installs the package with `pip install --user` and drops a
`.desktop` entry, so Sugar Next also appears in your normal app menu.

### Option 2: plain pip

```sh
pip install ./sugar-next     # from the monorepo root
sugar-next
```

### Option 3: container (no host install)

```sh
cd sugar-next
podman build -t sugar-next -f Containerfile .
podman run --rm \
  -e WAYLAND_DISPLAY -e XDG_RUNTIME_DIR \
  -v "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY:$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" \
  --userns=keep-id \
  sugar-next
```

The container shares your host Wayland compositor socket — the shell
opens as a regular window.

## Using the shell

- **App Grid** — every application on the system, alphabetized. Type in
  the search bar to filter instantly; click an icon to launch it.
- **Frame** — press **F6** (Sugar's classic frame key) or push the
  pointer into the **top-right hot corner**. The Frame shows your pinned
  favorites and the apps launched this session.
- **Pin favorites** — right-click any grid icon → *Pin to Frame
  favorites*. Right-click a Frame icon for its palette (unpin, and
  placeholder actions for what's coming). Favorites persist across
  sessions in `~/.local/share/sugar-next/favorites.json`.

## Writing an extension

Drop a `.py` file in `~/.local/share/sugar-next/extensions/` and restart
the shell:

```python
# ~/.local/share/sugar-next/extensions/hello.py

def on_shell_start():
    print("shell is up")

def on_app_launch(app_id, app_info):
    print(f"launching {app_id}")
```

That is the whole thing. Hooks are synchronous and best-effort: a broken
extension is logged and skipped, never crashing the shell or the other
extensions.

Working examples in [examples/extensions/](examples/extensions/):

| Extension | What it shows |
|-----------|---------------|
| `logger.py` | The minimum viable extension (~8 lines) |
| `launch-counter.py` | Persisting state (JSON launch counts) |
| `journal.py` | **The opt-in Journal** — records launches to SQLite. Installing it *is* the opt-in. |

Full API reference: [specbook/docs/sugar-next-extensions.md](../specbook/docs/sugar-next-extensions.md).

## Development

```sh
pip install -e ./sugar-next          # editable install
cd sugar-next && python3 -m pytest   # run the test suite
```

Layout:

```
sugar_next/
├── shell/            # main.py (Gtk.Application), app_grid.py, frame.py
├── bundles/          # desktop_bundle.py — wraps .desktop entries
└── api/              # hooks.py — extension scanner + dispatcher
examples/extensions/  # logger, launch-counter, journal
tests/                # pytest suite
Containerfile         # OCI image
bootstrap.sh          # pip install + desktop entry
docs/demo.mp4         # 20-second scripted demo
```

## Roadmap

Near-term, in rough order (tracked as OpenSpec changes in the monorepo,
see `openspec/changes/sugar-next/`):

- **Universal window listing in the Frame** via the wlroots
  `wlr-foreign-toplevel-management` protocol (Wayfire, Sway, labwc, …).
- **Richer Journal events** via Zeitgeist as an event source, keeping
  SQLite as the publish store.
- **More hooks** (`on_app_close`, …) driven by real extension usage —
  not speculation.
- **XO activity compat layer** — run legacy activities beside system
  apps, if and when someone wants it.

## Status

Early but working prototype: shell, App Grid with search, launch
pipeline, extension API, Frame v0, opt-in Journal, pip + OCI packaging,
and a passing test suite. Driven by the `sugar-next` OpenSpec change in
the [sugar-monorepo](https://github.com/icarito/sugar-monorepo) workspace.

License: GPL-3.0-or-later, like the rest of Sugar.
