# Sugar Next — A Learning Shell for Everyday Computing

## What this is

Sugar Next is a **sibling project** to the classic Sugar desktop, not a fork
and not a replacement. It lives under the [Sugar Labs](https://www.sugarlabs.org/)
umbrella and leaves the `sugar` (jarabe) repository completely untouched.
PR #1019 (the GTK4 port of the classic shell) continues on its own track.

Sugar Next is a place to explore what a modern, low-floor learning
environment could look like — using the technologies available today
(GTK4, Wayland, Python, XDG) — while the classic stack continues to serve
the XO hardware and existing deployments.

## Rationale

Sugar's founding insight was the **low floor**: a child could look inside
their computer and change it. Twenty years on, the stack that carried that
idea has quietly raised the floor out of reach:

- **GTK3 + X11** — both deprecated upstream. The GTK4 port of the shell
  (PR #1019) stalled on environment friction, not on technical difficulty:
  nobody could easily *run* what they were porting.
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
point some of it at *evolving* the environment instead of only maintaining
it.

Full design principles: [HIG.md](HIG.md).

### What Sugar Next deliberately does not do

- Touch the `sugar` repo, jarabe, or PR #1019 — the legacy shell stays
  exactly as it is.
- Migrate existing XO activities to a new API (a compat layer may come
  later, if the community wants it).
- Reimplement legacy mesh collaboration (the protocols are specific to the
  XO hardware and are not being recreated here).

## Quick start

Requires GTK4 and PyGObject from your distro:

| Distro | Command |
|--------|---------|
| Fedora | `sudo dnf install python3-gobject gtk4` |
| Debian/Ubuntu | `sudo apt install python3-gi gir1.2-gtk-4.0` |
| Arch | `sudo pacman -S python-gobject gtk4` |

```sh
git clone https://github.com/sugarlabs/sugar-next.git
cd sugar-next/sugar-next
./bootstrap.sh
sugar-next
```

> Note: the `sugar-next/` directory inside the repo is the actual project.
> Clone the whole repo, then `cd sugar-next/sugar-next` to find the shell.

For Podman, pip install, and development instructions see the full
[HIG.md](HIG.md) and the `openspec/` change documents.

## Status

Early but working prototype with:

- Pluggable Home View (desktop grid, app grid, search-first layouts)
- Settings panel (background, accent color, contrast, layout selector)
- Extension API with 5 hooks (on_shell_start, on_app_launch, on_app_close, on_peer_join, on_peer_leave)
- Frame with wlr-foreign-toplevel-management window listing
- Opt-in Journal extension (SQLite)
- Peer chat demo extension
- XDG Base Directory compliance
- Color token system (`--sn-*` CSS custom properties)
- StatusNotifierItem and D-Bus name registration

Everything tracked as OpenSpec changes under `openspec/changes/`.

## Acknowledgements

- **James Cameron (Quozl)** — for the green light to bring Sugar Next under
  the Sugar Labs umbrella, and for his decades of stewardship of the Sugar
  platform.
- **Walter Bender** — for the original vision of Sugar, and for keeping the
  educational mission alive through all these years.
- **Martin Abente (tchx84)** — for the Sugarapp/Flatpak work that proved
  Sugar activities can live outside the classic shell, and for Endless OS
  inspiration.
- **The Sugar Labs community** — the GSoC students, the sugar-devel
  regulars, and everyone who has contributed to keeping this project going
  since 2006.
- **Endless OS Foundation** — for demonstrating that a desktop-grid launcher,
  knowledge apps, and offline-first content can work beautifully for
  first-time computer users.
- **Sebastian Silva (icarito)** — for the exploration, the agentic
  prototyping, and the conviction that there is still room for a learning
  shell in 2026.
- **Pliaget** — the constructionist design agent that helped shape the HIG,
  the Home View layouts, and the extension API.

License: GPL-3.0-or-later, like the rest of Sugar.
