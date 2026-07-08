---
name: sugar-debugging
description: Use when the user wants to debug a running Sugar jarabe instance, attach a remote debugger, profile GTK memory usage, trace GTK signal handlers, or diagnose crashes in Sugar shell or toolkit code.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# Sugar Debugging

Techniques for debugging Sugar jarabe and sugar-toolkit-gtk4 at runtime,
including remote debugger attachment, GTK signal tracing, memory profiling,
and Wayland protocol debugging.

## Attaching debugpy to running jarabe

For deep debugging of jarabe logic (not widget layout — that's the GTK
inspector's job), attach Python's debugger to the running process:

### Setup (one-time per venv)

```bash
source repos/sugar-toolkit-gtk4/.venv/bin/activate
pip install debugpy
```

### Launch with debugpy listener

```bash
cd repos/sugar
WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" \
  LD_LIBRARY_PATH="$HOME/.local/lib:$LD_LIBRARY_PATH" \
  GI_TYPELIB_PATH="$HOME/.local/lib/girepository-1.0:$GI_TYPELIB_PATH" \
  GSETTINGS_SCHEMA_DIR="$HOME/.local/share/glib-2.0/schemas" \
  SUGAR_GROUP_LABELS="$(pwd)/data/group-labels.defaults" \
  SUGAR_MIME_DEFAULTS="$(pwd)/data/mime.defaults" \
  SUGAR_ACTIVITIES_HIDDEN="$(pwd)/data/activities.hidden" \
  ../sugar-toolkit-gtk4/.venv/bin/python3 -m debugpy --listen 5678 --wait-for-client \
  -c "import jarabe.main"
```

Then attach from VS Code with this launch configuration (`.vscode/launch.json`):

```json
{
    "name": "Attach to jarabe",
    "type": "debugpy",
    "request": "attach",
    "connect": { "host": "localhost", "port": 5678 },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}/repos/sugar/src",
            "remoteRoot": "."
        }
    ]
}
```

Without `--wait-for-client`, debugpy starts listening but jarabe proceeds
booting — useful for setting breakpoints that trigger mid-flow rather than
at startup.

For breakpoints that fire in `sugar-toolkit-gtk4` modules, add a second
`pathMappings` entry pointing at `repos/sugar-toolkit-gtk4/src`.

## Breakpoint strategies for GTK signal handlers

GTK signal handlers run inside `Gtk.main()` / `Gtk.Application.run()`, which
is a C-level GLib main loop — not a Python call chain. Debuggers need
special handling.

### Breakpoint inside a signal handler

Put `breakpoint()` directly in the handler:

```python
def _on_activate(self, widget):
    breakpoint()  # hits when user clicks the button
    self._launch_activity()
```

Works fine with debugpy — the GLib main loop yields to Python's signal
dispatch, which is a regular Python frame.

### Tracing which handlers fire without breakpoints

```python
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

def trace_handler(gobject, signal_name, *args):
    print(f"[TRACE] {gobject.__gtype__.name} ::{signal_name}"
          f" args={args[:3]}...")

# For a specific widget:
button.connect("clicked", trace_handler)

# For all managed signals on a widget (requires connecting to each):
for signal_id in GObject.signal_list_ids(type(widget)):
    name = GObject.signal_name(signal_id)
    if name not in ("notify",):  # skip noisy property notifies
        widget.connect(name, trace_handler, name)
```

### Break on a GObject property change

Use `GObject.Object.connect("notify::property-name", ...)` with a
breakpoint-carrying handler:

```python
def _on_size_change(obj, pspec):
    if new_size < 100:  # conditional: only break when interesting
        breakpoint()

window.connect("notify::default-width", _on_size_change)
```

## Memory profiling for GTK apps (leak detection)

GTK4 widget leaks are common in Python because widgets hold C memory that
Python's GC doesn't always account for.

### Using sys.gettotalrefcount (debug builds only)

If the Python was built with `--with-pydebug`:

```python
import sys
before = sys.gettotalrefcount()
# ... do suspect operation ...
after = sys.gettotalrefcount()
print(f"Ref count delta: {after - before}")
```

### Using GObject reference tracking

```python
import gc
from gi.repository import GObject, Gtk

def count_gobjects():
    """Count all live GObject instances in the process."""
    gobjects = [o for o in gc.get_objects() if isinstance(o, GObject.Object)]
    by_type = {}
    for o in gobjects:
        t = o.__gtype__.name
        by_type[t] = by_type.get(t, 0) + 1
    for t, c in sorted(by_type.items(), key=lambda x: -x[1])[:20]:
        print(f"  {t}: {c}")
    print(f"  Total GObjects: {len(gobjects)}")
```

Call `count_gobjects()` before and after suspect operations (opening a
dialog, switching views, launching/shutting down an activity). A growing
count without corresponding drops = likely leak.

### Checking for floating references

GTK4 widgets are born "floating" (their ref is owned by the container
that receives them). If you fail to `append()` / `set_child()` a widget,
it floats and leaks. This pattern leaks:

```python
label = Gtk.Label(label="leaked")  # floating, never added to a parent
return  # leaked: no container owns the ref
```

Fix by always parenting widgets or using `GObject.Object.ref_sink()`
followed by `unref()` when you must create widgets without adding them.

### GTK_DEBUG for memory

```bash
GTK_DEBUG=interactive     # inspector's "Statistics" tab shows object counts
GTK_DEBUG=no-css-cache    # bypass CSS cache to isolate CSS-related leaks
GTK_DEBUG=snapshot        # dump GtkSnapshot create/destroy pairs
```

## Reading GtkInspector output (non-interactive)

The inspector can also run as a one-shot dump without the interactive UI:

```bash
GTK_DEBUG=no-pixel-cache GTK_DEBUG=updates python3 app.py 2>&1 | grep -i gtk
```

- `GTK_DEBUG=updates`: prints every widget that gets size-allocated or
  drawn, useful for finding over-redraw.
- `GTK_DEBUG=layout`: prints layout size-allocate details.
- `GTK_DEBUG=no-pixel-cache`: forces full redraws (makes update traces
  more predictable).

Combine for diagnostics:

```bash
GTK_DEBUG=interactive GTK_DEBUG=layout \
  WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" ../sugar-toolkit-gtk4/.venv/bin/python3 \
  -c "import jarabe.main"
```

## Wayland protocol debugging (WAYLAND_DEBUG=1)

When jarabe runs under a nested Wayfire session, the Wayland protocol
between jarabe (client) and Wayfire (compositor) can be traced:

```bash
WAYLAND_DEBUG=1 WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" ../sugar-toolkit-gtk4/.venv/bin/python3 \
  -c "import jarabe.main" 2> wayland_trace.log
```

The log shows every Wayland protocol message:
- `wl_surface@12.attach(...)` — buffer attachment
- `wl_surface@12.commit()` — surface state applied
- `xdg_toplevel@15.configure(...)` — compositor resize/move requests
- `wl_keyboard@17.key(...)` — key events
- `zwlr_layer_surface_v1@18.configure(...)` — layer-shell sizing

Filter the log for specific objects or protocols:

```bash
grep "wl_surface@" wayland_trace.log | head -50    # surface lifecycle
grep "xdg_toplevel@" wayland_trace.log | head -50  # window management
grep "zwlr_layer_surface" wayland_trace.log        # layer-shell (panel, frame)
grep "error" wayland_trace.log                     # protocol errors (crashes!)
```

Common protocol errors to look for:
- `wl_display@1.error(...)` — fatal protocol violation, kills client
- Buffer attach without commit → surface doesn't update
- Commit with mismatched buffer scale → visual corruption
- Layer-shell configure without ack → compositor waits forever

## Catching GTK/GObject criticals and warnings

GTK logs non-fatal errors to stderr through GLib. Make them fatal to
break into the debugger at the source of the problem:

```bash
G_DEBUG=fatal-warnings G_DEBUG=fatal-criticals \
  WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" ../sugar-toolkit-gtk4/.venv/bin/python3 \
  -c "import jarabe.main"
```

This traps GLib warnings (GObject property type mismatches, CSS parse
errors) and criticals (null widget passed where non-null expected,
broken CSS node hierarchy) as crashes so the debugger can inspect the
call stack.

For less drastic logging, use `G_MESSAGES_DEBUG=all` to see all GLib
domain messages without making them fatal.

## Notes

- debugpy requires the user to confirm before connecting (VSCode will
  prompt). In CI, use `debugpy.listen()` + `debugpy.wait_for_client()`
  with a timeout.
- `WAYLAND_DEBUG=1` produces massive output for any real session
  (megabytes per second) — use it for short, targeted traces, not for
  running full jarabe. Start jarabe, trigger the suspect interaction,
  then kill it.
- GTK signal handler tracing with `breakpoint()` works in regular
  handlers but NOT in `Gtk.EventController` callbacks connected via GI
  (the C→Python bridge wraps those differently). For event controllers,
  use `print()` or a logging call instead.
- The GtkInspector's "Statistics" tab is the quickest way to spot a
  widget leak: open it once right after startup, then again after the
  suspect operation, and compare `GtkLabel: 47 → 94` etc.
