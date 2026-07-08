---
name: gtk4-widget-inspector
description: Use when the user wants to inspect GTK4 widget trees at runtime to understand widget hierarchy, diagnose layout or sizing issues, or explore GObject properties — in any GTK4 app including Sugar jarabe, sugar-toolkit-gtk4 activities, or Casilda-hosted windows.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# GTK4 Widget Inspector

Techniques for exploring GTK4 widget trees at runtime without source-code
walking. The GTK4 interactive debugger is built into the toolkit itself — no
separate tool install needed.

## Enabling the inspector (interactive)

Set `GTK_DEBUG=interactive` before launching any GTK4 app. This enables the
built-in GtkInspector, accessible via Ctrl+Shift+D or right-click → "Inspect":

```bash
GTK_DEBUG=interactive python3 app.py
```

For jarabe in nested Wayfire:

```bash
GTK_DEBUG=interactive WAYLAND_DISPLAY=wayland-1 SUGAR_NO_FULLSCREEN=1 \
  PYTHONPATH="src" \
  ../sugar-toolkit-gtk4/.venv/bin/python3 -c "import jarabe.main"
```

The inspector window opens as a separate toplevel. It shows:

- **Objects tab:** full widget tree with CSS node names, type names, and
  address. Click any widget to highlight it on screen.
- **Properties tab:** all GObject properties for the selected widget, with
  live read/write. Change `halign`, `vexpand`, `margin-top`, etc. and see
  the result immediately.
- **CSS tab:** applied CSS nodes, style properties, and a live CSS editor
  that applies rules as you type.
- **Resources tab:** loaded icons, images, themes.
- **Actions tab:** widget actions (`action-name`) and shortcuts.
- **Size Groups, Data, General tabs:** sizing info, `g_object_set_data`
  entries, and global GTK settings.

## Using gtk4-widget-factory for standalone exploration

GTK4 ships `gtk4-widget-factory` as a demo/widget gallery. Useful for
testing how a specific widget behaves in isolation:

```bash
GTK_DEBUG=interactive gtk4-widget-factory
```

Common patterns to test here before applying to Sugar code:
- `Gtk.ListView` with `Gtk.SignalListItemFactory` and `Gtk.Box` rows
- `Gtk.Stack` with `Gtk.StackSidebar`
- `Gtk.Popover` / `Gtk.PopoverMenu`
- `Gtk.DropDown` / `Gtk.ComboBoxText` replacement

## Dumping widget trees programmatically

When the interactive inspector isn't feasible (headless tests, CI, or
nested compositor environments where the inspector window can't open):

```python
def dump_tree(widget, indent=0):
    """Recursively print a widget tree to stdout."""
    name = widget.get_name() or "(unnamed)"
    klass = type(widget).__name__
    alloc = widget.get_allocation()
    print(f"{'  ' * indent}{klass}[{name}] "
          f"visible={widget.get_visible()} "
          f"at=({alloc.x},{alloc.y}) size={alloc.width}x{alloc.height}")
    child = widget.get_first_child()
    while child:
        dump_tree(child, indent + 1)
        child = child.get_next_sibling()

# Usage: dump_tree(window) after window.present()
```

For finding a specific widget by CSS name or type:

```python
def find_widget_by_css(root, css_name, klass=None):
    """Return first matching widget, or None."""
    if root.get_css_name() == css_name:
        if klass is None or isinstance(root, klass):
            return root
    child = root.get_first_child()
    while child:
        result = find_widget_by_css(child, css_name, klass)
        if result:
            return result
        child = child.get_next_sibling()
    return None
```

## D-Bus introspection of running Sugar

Sugar exposes several D-Bus interfaces that let you inspect running state
without attaching a debugger:

```bash
# List all Sugar-related names on the session bus
dbus-send --session --dest=org.freedesktop.DBus \
  --type=method_call --print-reply /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames | grep -i sugar

# Introspect the shell object
dbus-send --session --dest=org.sugarlabs.Shell \
  --type=method_call --print-reply /org/sugarlabs/Shell \
  org.freedesktop.DBus.Introspectable.Introspect
```

Common Sugar D-Bus interfaces:
- `org.sugarlabs.Shell` at `/org/sugarlabs/Shell` — activity launching,
  bundle registry, preferences.
- `org.sugarlabs.Activity` at `/org/sugarlabs/Activity/<id>` — individual
  activity lifecycle (start/stop/share/join).
- `org.sugarlabs.Journal` — datastore access for Journal entries.
- `org.sugarlabs.APISocket` — the Sugar API socket used by activities to
  call shell services.

Use `d-feet` (graphical) or `busctl --user tree` (CLI) for interactive
exploration.

## Reading the GObject type system

At the Python level, every widget exposes its GObject type chain:

```python
>>> from gi.repository import Gtk, GObject
>>> b = Gtk.Box()
>>> type(b).__mro__  # Python MRO: the Python wrapper classes
>>> b.__gtype__.name  # 'GtkBox'
>>> b.__gtype__.parent.name  # 'GtkWidget'

# Iterate all properties:
>>> props = [p.name for p in Gtk.Box.props]
>>> print(props)

# Iterate all signals:
>>> signals = [s.name for s in GObject.signal_list_ids(Gtk.Box)]
>>> print(signals)
```

For unknown widgets (from GI loading), introspect at runtime:

```python
from gi.repository import GObject, Gtk

# Load a dynamically loaded type by name
gtype = GObject.type_from_name("SugarGrid")
if gtype != GObject.TYPE_INVALID:
    klass = GObject.type_name(gtype)
    # can now gi.repository.require / import_by_name
```

## Notes

- `GTK_DEBUG=interactive` works with nested Wayfire — the inspector
  window opens as a separate GTK4 toplevel inside the same Wayfire
  session. If you can't see it, check Wayfire's workspace switching
  or window stacking.
- The inspector does not work with `GTK_DEBUG=interactive` inside a
  Casilda-embedded client surface (no separate toplevel to open). Use
  programmatic tree dumping for those cases.
- CSS node names are not 1:1 with widget class names — a `Gtk.Button`
  CSS node is `button`, not `GtkButton`. Check the Objects tab to see
  the real names.
