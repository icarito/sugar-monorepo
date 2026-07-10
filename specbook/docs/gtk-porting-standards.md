# GTK Porting Standards

Reference for GTK3→GTK4/PyGObject migration work in the Sugar stack. Written
so real blockers already found in this workspace (both environment/process
ones and, as of 2026-07-08, real code-level gaps — see "jarabe cannot start
yet" below) aren't rediscovered the hard way.

## Status of the existing attempt: sugar PR #1019

- **State:** open, marked **draft**, branch `gtk4-port` off `master`. Opened
  2026-01-21, last updated 2026-06-03 — stalled for over a month as of
  2026-07-08.
- **Author:** chimosky (repo member). Explicitly paused: *"I'm pushing
  because I want to take a break from looking at this, anyone is welcome to
  build on this."* No maintainer approve/request-changes review has landed —
  only informal contributor guidance in comments.
- **Size/shape:** 133 files changed, +1026/-1061 — broad but mechanical
  (`Gtk.VBox`/`Gtk.HBox` → `Gtk.Box`, `Gdk.Screen` usages replaced, etc.),
  not a rewrite. Touches nearly all of `jarabe`: `desktop/`, `frame/`,
  `journal/`, `controlpanel/`, `model/`, `view/`, `intro/`, plus
  `extensions/cpsection/*`, `extensions/deviceicon/*`, `bin/sugar-launch`,
  `bin/sugar-install-bundle`, `autogen.sh`/`configure.ac`, `tests/`.

## The real blocker: environment, not architecture

Every external contributor who tried to pick this PR back up
(vyagh, D-I-R-M, per PR comments) got stuck on **how to run and test the
shell under GTK4**, not on code review disagreements:

- Sugar traditionally runs as its own X11 session; there's no documented,
  repeatable way to run the *full shell* (not just the toolkit) under GTK4.
- The author suggests **Casilda** (a lightweight Wayland compositor from
  GNOME, `jpu/casilda`) as the way to test it, but no setup instructions
  exist for that combination.
- `sugar-ext` is needed for full testing and isn't part of the standard
  clone set.
- Only Nix flake / Flatpak setups existed for the *toolkit* alone
  (`sugar-toolkit-gtk4`), not for the shell.

**Implication for this workspace:** before resuming code-level porting work,
the first real change should be closing this environment gap — a
documented, reproducible way to build and run the `gtk4-port` branch under
Casilda (or an equivalent). Treat this as its own OpenSpec change, separate
from any code migration.

## Remaining known code gaps (from PR discussion)

- Leftover GTK3 patterns not yet converted: `Gtk.VBox`/`Gtk.HBox`,
  `Gdk.Screen` usages (confirmed present by a reviewing contributor).
- Watch for Python path differences across Debian version upgrades when
  testing via sugar-live-build.
- `git pull --unshallow` each repo before pushing changes back, per the
  author's guidance to contributors — shallow clones from some setups
  caused push friction.

## Toolkit-level GTK4 work is where the momentum actually is

`sugar-toolkit-gtk4` (separate repo) is a ground-up reimplementation of the
toolkit, not a port — and it's the most active repo in the whole org. Any
shell-level porting work should track what conventions that repo has already
settled on (modern `pip install -e .` + Makefile workflow, current Python
practices) rather than reinventing them at the shell layer.

## Conventions to follow when this work resumes

1. Prefer the migration patterns already used in PR #1019 for mechanical
   API swaps (`Gtk.Box` over `Gtk.VBox`/`Gtk.HBox`, etc.) rather than
   inventing new idioms — consistency with the existing draft reduces
   review friction if it's ever merged upstream.
2. Any new environment/build tooling introduced for GTK4 testing should be
   documented in this file and in [[sugar-stack]], not only in a PR
   description that can get lost.
3. Small, reviewable sub-PRs against `gtk4-port` (or its resumed equivalent)
   rather than one large diff — per [[base-standards]] rule 1.

## Sugar Next session target: Hyprland

Sugar Next targets Hyprland as its Wayland session compositor. In a real
Sugar Next login, Hyprland owns tiling, focus, workspaces, and the native
stripe/bar while Sugar Next runs as the session shell and renders the Home
View plus Frame overlay.

When `HYPRLAND_INSTANCE_SIGNATURE` is present, Sugar Next reads window and
focus state through `hyprctl clients -j`, `hyprctl activewindow -j`, and
`hyprctl workspaces -j`; the older `TopLevelTracker` client is kept as a
development fallback for non-Hyprland compositors such as Wayfire, Sway, or
GNOME/Mutter. Nested development uses `AQ_BACKENDS=wayland` through
`sugar-next/dev/run-hyprland-nested.sh`. Native login sessions should not
set `AQ_BACKENDS`; install a `/usr/share/wayland-sessions/sugar-next.desktop`
entry that runs `Hyprland -c /etc/sugar-next/hyprland.lua`, using
`sugar-next/session/hyprland.lua` as the template. Hyprland's Lua config
API uses `hl.on("hyprland.start", ...)` plus `hl.exec_cmd(...)` for
autostart on the tested 0.55 series.

Sugar Next prefers GTK layer-shell for its own root surface. If a GI
namespace such as `Gtk4LayerShell` or `GtkLayerShell` is installed, the main
window is initialized as a layer surface anchored to every edge; otherwise
it falls back to a regular `xdg_toplevel` and Hyprland fullscreen window
rules make it behave like the shell. With `gtk4-layer-shell` on Arch/CachyOS,
PyGObject also needs the package's preload helper so `libgtk4-layer-shell`
loads before `libwayland`; the dev runner exports
`LD_PRELOAD=/usr/lib/liblayer-shell-preload.so` for the Sugar Next process
when that file exists.

For development under GNOME, the Hyprland Wayland backend does not request a
host titlebar itself. `gamescope` can be tried with
`SUGAR_NEXT_DECORATED_HOST=1`, but it is not the default because current
gamescope may expose a newer `wl_compositor` version than this Hyprland /
Aquamarine build accepts. The stable default runs Hyprland directly.

## Working dev environment: Casilda + sugar-toolkit-gtk4 (validated 2026-07-08)

The environment gap described above is now partially closed. OpenSpec
change `gtk4-dev-environment` (see `openspec/changes/gtk4-dev-environment/`,
or `openspec/specs/` once archived) validated the toolchain end-to-end:
Casilda builds and embeds a real `sugar-toolkit-gtk4` activity in a window,
on this host (CachyOS, native Wayland session).

**What this proves:** the build toolchain (Meson, wlroots, GTK4, Python
packaging) works together on a modern Linux laptop, and a `sugar-toolkit-gtk4`
activity can render inside a Casilda-hosted window via in-process
GObject Introspection — no exotic two-process/socket wiring needed.

**What this does NOT prove:** that the full `jarabe` shell (PR #1019) can
run this way. Casilda embeds one client surface; it has no window-manager
or layer-shell protocol support. Running `jarabe` — which expects to *be*
the window-managing compositor — is a separate, unsolved problem. Treat
this section as toolchain validation, not shell-readiness.

### Working procedure

Dependencies on CachyOS/Arch — most were likely already installed if
you have a GTK4 dev setup; the one probably missing is `wlroots0.20`:

```bash
sudo pacman -S wlroots0.20   # meson, ninja, gtk4, pixman, wayland,
                              # libxkbcommon, gobject-introspection,
                              # python-gobject were already present
sudo pacman -S gtk4-demos    # optional, only needed to reproduce the
                              # upstream Casilda example as a smoke test
```

Versions confirmed working: Meson 1.11.1, Ninja 1.13.2, GTK4 4.22.4,
wlroots0.20 0.20.1, pixman 0.46.4, wayland 1.25.0, libxkbcommon 1.13.2,
gobject-introspection 1.86.0, python-gobject 3.56.3.

**Build Casilda** (into a user-local prefix, no `sudo` needed for this part):

```bash
git clone https://gitlab.gnome.org/jpu/casilda repos/casilda
cd repos/casilda
meson setup --prefix="$HOME/.local" _build .
ninja -C _build install
```

**Build sugar-toolkit-gtk4** (in a venv with system site-packages, so
PyGObject/`gi` resolve against the system's compiled GI bindings instead
of trying to rebuild them from PyPI):

```bash
git clone https://github.com/sugarlabs/sugar-toolkit-gtk4 repos/sugar-toolkit-gtk4
cd repos/sugar-toolkit-gtk4
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e ".[test]"
make test   # 380/385 pass — see "Known environment quirk" below
```

**Run the embedded demo** (from an active graphical Wayland session —
`echo $WAYLAND_DISPLAY` should print something like `wayland-0`):

```bash
export LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="$HOME/.local/lib/girepository-1.0:$GI_TYPELIB_PATH"
python3 specbook/demos/casilda_sugar_demo.py
```

This opens a GTK4 window with a `Casilda.Compositor()` widget as its
child, which spawns `repos/sugar-toolkit-gtk4/examples/basic_activity.py`
(via that repo's own venv interpreter) as the embedded Wayland client.
`SimpleActivity`-based examples need `SUGAR_BUNDLE_PATH`,
`SUGAR_BUNDLE_NAME`, `SUGAR_BUNDLE_ID` set (see
`examples/activity/activity.info` in that repo) — the demo script sets
these via `spawn_async`'s `envp` parameter.

### Known environment quirk: icon theme test failures

`sugar-toolkit-gtk4`'s test suite has 5 failures in `test_combobox.py` on
this host, all tracing to `Gtk.IconTheme` resolving names like
`document-new` to `None`. Root cause: CachyOS ships those icons under the
`AdwaitaLegacy` theme, not the default `Adwaita` theme GTK4's icon lookup
checks by default — confirmed the files exist on disk
(`/usr/share/icons/AdwaitaLegacy/...`), just under an unindexed theme.
This is **not a toolkit bug** — no source was patched. If you hit this on
another distro, check which theme provides legacy Adwaita icon names
before assuming it's a regression.

## Windowed jarabe: SUCCESS (2026-07-08, change `windowed-jarabe`)

**jarabe (gtk4-port branch) now starts, runs, and renders real content
inside a nested Wayfire session on this host.** This closes the
environment gap described above for the intro/onboarding screen; the
full Home View/Frame/Journal path is not yet exercised (see Known
limitations below).

### Why Wayfire, not Casilda

Running `jarabe` fully embedded in Casilda (one client surface, no
window-management) was ruled out — see the previous section. **Wayfire**
was used instead: an actively maintained wlroots compositor with real
multi-window management, wlr-layer-shell support, and documented
nested/windowed operation (unlike Cage, which is kiosk-only with no
layer-shell; unlike GNOME Shell `--nested`, which is Mutter-specific and
reportedly broken in recent GNOME releases).

**Prior art**: [sugar#929](https://github.com/sugarlabs/sugar/issues/929)
("Launch sugar in a window", open since 2020) already diagnosed that
running Sugar in a window needs jarabe itself to change — skip
fullscreen, don't start its own window manager/session, let the host
compositor manage focus.

### What was implemented

- **`SUGAR_NO_FULLSCREEN=1`** environment variable (matching jarabe's
  existing env-var-based config pattern — there's no argparse/CLI-flag
  convention anywhere in this codebase). When set:
  - `jarabe/main.py::_start_window_manager()` skips spawning its own
    `mutter --wayland` and skips mutating global
    `org.gnome.desktop.interface` GSettings.
  - `jarabe/desktop/homewindow.py`'s `HomeWindow` uses a fixed 1024×768
    default size instead of the full screen, and skips the
    screen-size-tracking callback and the `DESKTOP` window-type hint.
- Wayfire confirmed working nested on this host (0.10.1, auto-detects
  `$WAYLAND_DISPLAY` and runs as a windowed Wayland client;
  `wf-config` 0.10.0, `wlroots0.19` 0.19.3).

### The blocker chain that had to be resolved (in order)

Getting from "doesn't import" to "renders on screen" required fixing
**both** pre-existing bugs in the `gtk4-port` branch/`sugar-toolkit-gtk4`
**and** completing genuinely missing pieces. None of this is
Wayfire/Casilda/windowed-mode-specific — it's what any attempt to run
`jarabe` (gtk4-port) at all requires, regardless of hosting approach.

**Missing toolkit pieces, added to `sugar-toolkit-gtk4`:**
- `src/jarabe/config.py` — Autotools-generated, never built in this dev
  setup; hand-written a dev-only version pointing at the checkout.
- `sugar4/activity/activityfactory.py` — direct namespace port from
  `sugar-toolkit-gtk3` (pure Python/D-Bus/subprocess, no GTK3/X11
  dependency, so a straight port, not a stub).
- `sugar4/activity/i18n.py` — same, direct port (`pgettext` and MO-file
  parsing, pure Python).
- `sugar4/ext.py` — pure-Python replacement for `SugarExt` (see below).
- `sugar4/gtk3compat.py` — GTK3-API compatibility shims (see below).

**The structural blocker: `SugarExt`/`SugarGestures` ABI conflict.**
`SugarExt` and `SugarGestures` (from `sugar-toolkit-gtk3`, installed via
Arch's `sugar-toolkit-gtk3` package) are compiled against GTK3. `jarabe`
(gtk4-port) already loads GTK4 first, and GObject Introspection refuses
to load two ABI-incompatible `Gtk` versions in one process. Resolved by
writing `sugar4/ext.py`: real working ports of the pieces that don't
depend on X11/GTK3 (`Grid` — pure arithmetic; `fat_set_hidden_attrib` —
plain Linux ioctl), and explicit, documented stubs (never silently
faking success) for the pieces that have no direct Wayland/GTK4
equivalent and need real design work later: `CursorTracker` (X11 XInput2
raw-event cursor hiding), `clipboard_set_with_data` (GTK3
`GtkClipboard` API, replaced by `Gdk.Clipboard`/`Gdk.ContentProvider` in
GTK4), `VolumeAlsa` (direct ALSA mixer access — should go through
PipeWire), `SwipeController`/`SwipeDirectionFlags` (GTK4 has a native
`Gtk.GestureSwipe` that could replace this properly).

**Also found and fixed, a real bug in `gtk4-port` unrelated to the
GTK3/GTK4 ABI split:** `main.py` required `SugarExt` version `'2.0'`,
which has never existed (upstream `master` correctly uses `'1.0'`).
Traced via `git diff origin/master origin/gtk4-port` to commit
`b9fdeefb` ("[WIP] Port to Gtk4") — an accidental version bump alongside
the GTK3→4 migration. Fixed in this workspace's checkout.

**GTK3 API removed in GTK4, needing mechanical fixes across many files**
(see `sugar4/gtk3compat.py` for the shims — monkey-patches installed
once via `gtk3compat.install()`, called early in `jarabe/main.py`,
instead of editing every call site):
- `Gtk.Alignment` (~15 sites, 8 files) — shimmed as a `Gtk.Box` subclass
  mapping xalign/yalign to halign/valign.
- `Gtk.Box.pack_start`/`pack_end` (157 sites, 24 files) — shimmed to
  `append()` + hexpand/vexpand + margin mapping.
- `Gtk.Widget.get_children()` (~21 files) — shimmed via
  `get_first_child()`/`get_next_sibling()` traversal.
- `Gdk.Screen` (~38 sites, 18 files, all `.width()`/`.height()`/
  `.get_default()`) — shimmed via `Gdk.Display.get_monitors()`.
- `Gtk.Widget.set_border_width()` (11 files) — shimmed to four
  `set_margin_*` calls.
- `Gtk.HButtonBox`/`Gtk.ButtonBoxStyle` (4 files) — shimmed as a
  `Gtk.Box` subclass.
- `Gtk.Button.set_image()` (2 direct `Gtk.Button` call sites; ~30 other
  call sites are on `sugar4.graphics.menuitem.MenuItem`, which got its
  own `set_image()` added directly since it already manages its content
  box) — shimmed to wrap icon+label in a `Gtk.Box` child.
- Individually fixed (small enough not to need a shim): `Gtk.EventBox`/
  `Gtk.Bin` base classes (→ `Gtk.Box`) in ~10 classes across
  `expandedentry.py`, `detailview.py`, `colorpicker.py`,
  `activitieslist.py`, `projectview.py`, `notification.py`,
  `viewsource.py`, `gui.py`, `listview.py`, `iconview.py`,
  `framewindow.py`, `snowflakelayout.py`, `viewcontainer.py`; positional
  `Gtk.Label(text)`/`Gtk.Button(text)` constructor calls (GI requires
  keyword args in GTK4); `Gtk.STOCK_STOP` (stock items removed);
  `Gtk.Adjustment` `step_incr`/`page_incr` → `step_increment`/
  `page_increment`; `Gtk.HScale` → `Gtk.Scale(orientation=...)`;
  `'button-press-event'`/`'key-press-event'` signals → `Gtk.GestureClick`/
  `Gtk.EventControllerKey`; `Gdk.ModifierType.MOD1_MASK` →
  `.ALT_MASK`; `Gdk.Seat.get_slaves()` → `.get_devices()`.
- `SnowflakeLayout`/`ViewContainer` (`jarabe/desktop/`) implemented the
  full GTK3 `Gtk.Container` protocol (`do_realize`, `do_size_allocate`,
  etc.) for custom icon layout (circular "snowflake" arrangement,
  delegated-layout containers). GTK4 replaces that protocol with
  `Gtk.LayoutManager` — a different API. Stubbed to plain `Gtk.Box`
  packing (insertion order, no circular/delegated positioning) to keep
  the `add_icon()`/`remove()`/`set_layout()` call sites working; **the
  actual Home View / mesh view icon layout is not visually correct** as
  a result — this is real layout-code work for a future change.

**Two bugs in `jarabe/model/shell.py` found only by running the code:**
- `_window_added_cb`/`_window_removed_cb` called
  `window.get_type_hint()` (removed in GTK4 entirely — X11 window-manager
  hints have no Wayland equivalent). This code handles activity-window
  registration (Journal/app windows); disabled (`if False:`) rather than
  redesigned, since it needs a real replacement mechanism (explicit
  window-role tracking) — **activity window tracking is unverified/likely
  non-functional** until that's designed.
- **The actual root cause of "window renders as a blank gray box":**
  `ShellModel.add_window()` unconditionally did
  `window.set_child(self.compositor)` before adding *any* window —
  clobbering real content already set by `IntroWindow`/`HomeWindow`/
  `FrameWindow` (they all set their own child before being added). Found
  by bisecting: isolated tests of `IntroWindow` alone, `_IntroBox` alone,
  and `Casilda.Compositor()` alongside a plain `Gtk.Application` all
  rendered correctly; only the real `ShellModel.add_window()` reproduced
  the blank window. Likely intent (per the incomplete `spawn_async` call
  found in the same class) was for *activity* windows specifically to
  host the compositor so an activity process renders into it via
  Casilda — but nothing marks a window as an activity window at this
  point in the code, and shell UI windows already have real content.
  **Fixed**: only fall back to the compositor if `window.get_child() is
  None`. A real fix should explicitly distinguish activity windows from
  shell windows rather than relying on "has no child yet".

### Working procedure

```bash
# One-time: compile Sugar's GSettings schema into a user-local dir
mkdir -p ~/.local/share/glib-2.0/schemas
cp repos/sugar/data/org.sugarlabs.gschema.xml ~/.local/share/glib-2.0/schemas/
glib-compile-schemas ~/.local/share/glib-2.0/schemas/

# Launch nested Wayfire (from an existing Wayland session)
wayfire &            # auto-detects $WAYLAND_DISPLAY, prints which
                      # socket it created (e.g. "Using socket name wayland-1")

# Run jarabe pointed at that nested session
cd repos/sugar
WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  SUGAR_GROUP_LABELS="$(pwd)/data/group-labels.defaults" \
  SUGAR_MIME_DEFAULTS="$(pwd)/data/mime.defaults" \
  SUGAR_ACTIVITIES_HIDDEN="$(pwd)/data/activities.hidden" \
  PYTHONPATH="src" \
  LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH" \
  GI_TYPELIB_PATH="$HOME/.local/lib/girepository-1.0:$GI_TYPELIB_PATH" \
  GSETTINGS_SCHEMA_DIR="$HOME/.local/share/glib-2.0/schemas" \
  ../sugar-toolkit-gtk4/.venv/bin/python3 -c "import jarabe.main"
```

Result: the Wayfire window shows Sugar's onboarding screen (name/color/
gender/age entry) with real, visible content — confirmed visually.

### Known limitations of this validated path

- Only the **intro/onboarding flow** was exercised end-to-end (no Sugar
  profile existed on this host, so `jarabe` took the
  `_start_intro()` path). The Home View, Frame, and Journal — which need
  `_begin_desktop_startup()` — are unverified. Given the
  `_window_added_cb`/`get_type_hint()` disabling above, activity window
  tracking specifically is expected to need more work.
- D-Bus session services (Telepathy/mission-control, notifications,
  `apisocket`) are unverified — no full session/logind backing exists in
  this nested setup.
- `SnowflakeLayout`/`ViewContainer` icon positioning (Home View icon
  arrangement, mesh view) is a plain box-packing stub, not the real
  circular/delegated layout — visually incorrect if/when reached.
- Several stubbed pieces in `sugar4/ext.py` are explicitly non-functional
  (cursor auto-hide on touch, clipboard export, real ALSA volume, swipe
  gestures) — logged as warnings on use, not silent.

## Out of scope for now

- Redesigning activity-window tracking in `ShellModel` (replacing the
  disabled `get_type_hint()`-based logic in `_window_added_cb`/
  `_window_removed_cb` with an explicit window-role mechanism).
- Porting `SnowflakeLayout`/`ViewContainer` to a real `Gtk.LayoutManager`
  for correct icon positioning.
- Real GTK4-native implementations of the explicitly-stubbed
  `sugar4/ext.py` pieces (CursorTracker via Wayland pointer protocols,
  clipboard via `Gdk.Clipboard`/`Gdk.ContentProvider`, ALSA volume via
  PipeWire, swipe gestures via `Gtk.GestureSwipe`).
- Validating the Home View / Frame / Journal path (requires an existing
  Sugar profile, or clicking through the onboarding flow).
- A Sugar-specific GTK4 theme (the `sugar-72`/`sugar-100` GTK3 themes
  installed on this host don't apply to GTK4 at all — GTK4's theming
  model is entirely different. jarabe currently renders with the host's
  default GTK4 theme, no Sugar visual identity).
