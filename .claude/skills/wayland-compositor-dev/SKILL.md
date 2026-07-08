---
name: wayland-compositor-dev
description: Use when the user wants to set up or debug nested Wayfire for running Sugar jarabe, configure Wayfire plugins for Sugar's window management, trace Wayland protocol between Sugar and its compositor, or work with Casilda compositor widget for embedding activities.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# Wayland Compositor Development

Workflows for developing and debugging the Wayland compositor layer that
hosts Sugar jarabe — nested Wayfire for the full shell, Casilda compositor
widget for embedded activity windows, and the wlroots stack underneath.

## Nested Wayfire setup and debugging

Wayfire runs nested when `$WAYLAND_DISPLAY` is already set (i.e., you're
already in a Wayland session). It auto-creates a new socket (typically
`wayland-1`):

```bash
wayfire &
# Output: "Using socket name wayland-1"
```

### Verifying it's running

```bash
echo $WAYLAND_DISPLAY         # your host wayland socket
ls $XDG_RUNTIME_DIR/wayland-* # should see wayland-1 appear after wayfire starts
WAYLAND_DISPLAY=wayland-1 wayland-info  # list protocols + globals available
```

### Wayfire nested-specific quirks

- **Input grabbing fails silently** — the nested Wayfire can't grab the
  host's input devices. Sugar features that rely on global keyboard
  shortcuts (Frame key, screenshot) won't work the same way.
- **No hardware cursor** — the nested compositor inherits the host's
  cursor. Custom cursor themes or cursor-hiding (`CursorTracker` in
  `sugar4/ext.py`) have no effect.
- **Window decorations** — Wayfire's default `decoration` plugin draws
  server-side decorations on all windows. If jarabe windows look
  double-bordered, disable the plugin in `wayfire.ini`.
- **Workspace switching** — nested Wayfire gets its own workspace grid,
  independent of the host compositor. Use Super+arrows or configure
  `wayfire.ini`.

### wayfire.ini for Sugar development

Minimal config that disables noisy plugins for development:

```ini
# ~/.config/wayfire.ini
[core]
plugins = autostart close cube decoration expo fast-switcher \
          grid move place resize switcher vswitch wm-actions wrot \
          zoom

[autostart]
# No autostart panesls/backgrounds in dev mode

[wm-actions]
toggle_fullscreen = <super> KEY_F
toggle_always_on_top = <super> KEY_T

[input]
cursor_timeout = 0    # never hide cursor for dev
```

Turn off `animate`, `fade`, `blur`, `showrepaint` — these add visual noise
that obscures what jarabe is actually rendering vs. what Wayfire is
compositing on top.

### Debugging Wayfire itself

```bash
# See Wayfire's own log output
wayfire 2>&1 | tee wayfire.log &

# Enable wlroots logging
WLR_LOG=debug wayfire 2>&1 | tee wayfire_wlroots.log &
```

Common wlroots log patterns:
- `"no output found"` — no monitor/head detected (expected in nested mode)
- `"drmModeAtomicCommit"` — DRM errors (not relevant nested, ignore)
- `"failed to bind buffer"` — client sent invalid buffer, likely GTK/Wayland
  mismatch
- `"surface state mismatch"` — client committed inconsistent buffer/scale

## Casilda compositor widget usage

Casilda (`jpu/casilda` on GNOME GitLab) is a GTK4 widget that embeds a
wlroots compositor, letting you host Wayland clients inside a regular
GTK4 window. Sugar jarabe uses this to embed activity windows directly.

### Building from source

```bash
git clone https://gitlab.gnome.org/jpu/casilda repos/casilda
cd repos/casilda
meson setup --prefix="$HOME/.local" _build .
ninja -C _build install
```

Requires: `wlroots0.20`, `gtk4`, `meson`, `ninja` (see [[gtk-porting-standards]]
for exact versions confirmed working).

### Embedding a Casilda compositor in a GTK4 window

```python
import gi
gi.require_version("Casilda", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Casilda, Gtk

def on_activate(app):
    win = Gtk.ApplicationWindow(application=app, title="Embedded Compositor")
    compositor = Casilda.Compositor()
    win.set_child(compositor)
    compositor.spawn_async(
        "repos/sugar-toolkit-gtk4/.venv/bin/python3",
        "examples/basic_activity.py",
        envp=[
            "WAYLAND_DISPLAY=" + compositor.get_wayland_display_name(),
            "SUGAR_BUNDLE_PATH=examples/activity",
        ]
    )
    win.present()

app = Gtk.Application()
app.connect("activate", on_activate)
app.run()
```

Key Casilda API points:

- `Casilda.Compositor()` — the widget, creates its own wlroots backend.
- `compositor.get_wayland_display_name()` — returns the socket name clients
  connect to (e.g. `wayland-2`). Pass as `WAYLAND_DISPLAY` to spawned
  clients.
- `compositor.spawn_async(argv0, ...)`: spawns a child process for the
  embedded client. Accepts argv, envp, cwd, flags (from `GLib.SpawnFlags`).
  The compositor manages this child's lifecycle.
- `compositor.set_child(widget)` — **DO NOT** call this if the compositor
  is already managing its own internal surface stack. Casilda is a
  `Gtk.Widget` subclass, so it's a leaf node — use it as the child of a
  container, not as a container itself.

### Casilda inside jarabe

In Sugar's architecture (gtk4-port branch, `jarabe/model/shell.py`),
jarabe itself hosts a `Casilda.Compositor()` that manages activity
windows. Each activity spawns as a Wayland client into the compositor,
rather than being a direct widget child of the shell window. This is the
inverse of the toolkit-demo pattern above — jarabe is the compositor host,
not the client.

Known issue (from `windowed-jarabe` change): `ShellModel.add_window()`
unconditionally called `window.set_child(self.compositor)`, clobbering
shell UI windows that already had their own content. Fixed by only
falling back to the compositor when `window.get_child() is None`. See
[[gtk-porting-standards]].

## wlroots debugging

wlroots (the library Wayfire and Casilda are built on) has its own
debugging facilities:

```bash
# Trace all wlroots backend operations
WLR_LOG=debug wayfire 2>&1 | grep -E "(backend|output|render)"

# Trace DRM/KMS specifically
WLR_DRM_NO_ATOMIC=1   # fall back to legacy KMS API (last resort for GPU bugs)
WLR_RENDERER=pixman   # software rendering fallback (when GPU driver is suspect)
```

For Casilda specifically, since it's embedded in GTK4, wlroots uses
GTK4's rendering path (not direct DRM/KMS). The `WLR_RENDERER` variable
may still help for isolating whether a rendering artifact is from
wlroots or from GTK4.

### Checking wlroots version at runtime

```python
# In Python, via GI if wlroots exposes introspection (usually doesn't)
# Instead check the shared library:
import ctypes, ctypes.util
lib = ctypes.CDLL(ctypes.util.find_library("wlroots"))
# Version symbols are defines, not exported — check pkg-config instead:
```

```bash
pkg-config --modversion wlroots
# 0.20.1 (casilda uses 0.20; wayfire 0.10.x uses 0.19)
```

Note the version split: Casilda pins `wlroots0.20`, Wayfire 0.10.x
pins `wlroots0.19`. Both must be installed on the system — they're
separate binary packages that can coexist (different sonames).

## Wayland protocol tracing

Beyond `WAYLAND_DEBUG=1` (see the `sugar-debugging` skill), deeper
protocol-level debugging:

### wayland-scanner for protocol introspection

```bash
# List all protocols the compositor advertises
WAYLAND_DISPLAY=wayland-1 wayland-info | grep "^interface"

# Check if a specific protocol is available
WAYLAND_DISPLAY=wayland-1 wayland-info | grep -A5 "wlr_layer_shell"
```

### Common Sugar-relevant protocols

- `wlr_layer_shell_unstable_v1` — needed for Sugar's Frame (panel) and
  any always-on-top UI elements. If missing: Wayfire needs the `wrot`
  plugin, or Sugar needs a fallback to toplevel windows.
- `xdg_shell` / `xdg_wm_base` — standard window management. Every
  jarabe window uses this.
- `wp_viewporter` — fractional scaling. Affects HiDPI rendering in
  nested mode.
- `zwp_primary_selection_v1` — middle-click paste. Sugar's clipboard
  integration may need this.
- `wp_pointer_gestures_v1` — swipe/pinch. Relevant for touchscreen
  Sugar deployments, and for replacing Sugar's swipe gesture handling
  (currently stubbed in `sugar4/ext.py`).

### Recording and replaying protocol traces

```bash
# Record a session
WAYLAND_DEBUG=1 SUGAR_NO_FULLSCREEN=1 WAYLAND_DISPLAY=wayland-1 \
  ../sugar-toolkit-gtk4/.venv/bin/python3 -c "import jarabe.main" \
  2> wayland_trace.log

# Extract specific object timelines
grep "wl_surface@42" wayland_trace.log
```

## GTK4's Wayland backend configuration

GTK4 auto-selects Wayland when `$WAYLAND_DISPLAY` is set. Forced overrides:

```bash
GDK_BACKEND=wayland     # force Wayland (default when $WAYLAND_DISPLAY set)
GDK_BACKEND=x11         # force X11 (fallback, needs XWayland in nested mode)
GDK_BACKEND=wayland,x11 # prefer Wayland, fall back to X11
```

GDK debug flags relevant to compositor work:

```bash
GDK_DEBUG=gl-disable       # force software rendering (helpful for GPU driver bugs)
GDK_DEBUG=portals          # trace portal (screenshot, file chooser) usage
GDK_DEBUG=no-vsync         # disable vsync for faster iteration (tears!)
GDK_DEBUG=opengl           # trace GL calls
```

For diagnosing rendering in nested Wayfire:

```bash
GDK_DEBUG=gl-disable WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" ../sugar-toolkit-gtk4/.venv/bin/python3 \
  -c "import jarabe.main"
```

If jarabe renders correctly with software GL but not hardware GL, the
GPU driver or wlroots renderer is suspect.

## Notes

- Nested Wayfire inherits the host compositor's refresh rate. If jarabe
  animations look choppy, check your host's vsync configuration, not
  Wayfire's.
- Casilda's `spawn_async` creates real subprocesses — the embedded client
  is a separate Python interpreter. This means breakpoints in the client
  won't fire in the host process's debugger. Use debugpy on the client
  separately, or run the client without Casilda (directly in Wayfire)
  during debugging.
- The `Wayfire.ini` format changed across versions (0.8, 0.9, 0.10). Check
  `wayfire --version` and match the config syntax. The `[core]` and `plugins`
  sections shown here are for 0.10.x.
- For GPU/driver crashes in nested mode, the host compositor is unaffected —
  only the nested Wayfire/Casilda window will die. This makes nested
  development much safer than running Sugar as a real session.
