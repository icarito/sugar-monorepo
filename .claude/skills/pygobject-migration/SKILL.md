---
name: pygobject-migration
description: Use when the user wants to migrate Python GTK code from GTK3 to GTK4, specifically GTK3→4 API differences like Container→Box changes, pack_start→append, event signals→controllers, drawing model changes, or when using Sugar's gtk3compat.py shim layer.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# PyGObject GTK3 → GTK4 Migration

Reference for migrating Python GTK code from GTK3 to GTK4 in the Sugar
stack. Covers the common mechanical API changes, Sugar's compatibility
shim (`sugar4/gtk3compat.py`), and the design differences that require
real rewrites rather than search-and-replace.

## Quick reference: the most common changes

| GTK3 | GTK4 |
|------|------|
| `Gtk.VBox` / `Gtk.HBox` | `Gtk.Box(orientation=...)` |
| `box.pack_start(widget, expand, fill, pad)` | `box.append(widget)` + set `hexpand`/`vexpand`/`margin-*` on widget |
| `box.pack_end(widget, expand, fill, pad)` | `box.prepend(widget)` |
| `Gtk.Alignment(xalign=0.5, yalign=0.5, xscale=0, yscale=0)` | `Gtk.Box()` + `halign`/`valign` on child |
| `button.set_image(image_widget)` | `box = Gtk.Box(); box.append(image); box.append(label); button.set_child(box)` |
| `widget.get_children()` | iterate via `get_first_child()` / `get_next_sibling()` |
| `Gtk.EventBox` | `Gtk.Box()` or any widget (all widgets receive events in GTK4) |
| `widget.connect("button-press-event", handler)` | `Gtk.GestureClick` attached to widget |
| `widget.connect("key-press-event", handler)` | `Gtk.EventControllerKey` attached to widget |
| `widget.connect("draw", handler)` | `widget.set_draw_func(callback)` → receives `Gtk.Snapshot` |
| `Gdk.Screen.width()` / `.height()` / `.get_default()` | `Gdk.Display.get_monitors()` |
| `widget.set_border_width(n)` | `widget.set_margin_start(n); widget.set_margin_end(n); widget.set_margin_top(n); widget.set_margin_bottom(n)` |
| `Gtk.Button("label")` / `Gtk.Label("text")` | `Gtk.Button(label="label")` / `Gtk.Label(label="text")` (GI requires keyword args in GTK4) |
| `Gtk.HButtonBox` / `Gtk.ButtonBoxStyle` | `Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)` + per-child spacing |
| `Gtk.STOCK_*` items | removed — use named icons or custom labels |
| `Gtk.HScale` | `Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)` |
| `Gtk.Adjustment.step_incr` / `page_incr` | `.step_increment` / `.page_increment` |
| `Gdk.ModifierType.MOD1_MASK` | `Gdk.ModifierType.ALT_MASK` |
| `Gdk.Seat.get_slaves()` | `Gdk.Seat.get_devices()` |
| `window.get_type_hint()` | removed (X11-only, no Wayland equivalent) |

## Using sugar4/gtk3compat.py shim

Sugar's GTK4 port ships `sugar4/gtk3compat.py`, a monkey-patch layer that
reinstates common GTK3 APIs on top of GTK4, avoiding per-callsite rewriting.
Call once, early in startup:

```python
# In jarabe/main.py:
from sugar4 import gtk3compat
gtk3compat.install()
```

This adds to GTK4 classes:
- `Gtk.Alignment(*args, **kwargs)` — new class, subclass of `Gtk.Box`,
  maps `xalign`/`yalign` → `halign`/`valign`.
- `Gtk.Box.pack_start(child, expand, fill, padding)` — maps to `append()`
  plus hexpand/vexpand/margin settings.
- `Gtk.Box.pack_end(child, expand, fill, padding)` — maps to `prepend()`
  plus hexpand/vexpand/margin settings.
- `Gtk.Widget.get_children()` — returns list via traversal.
- `Gtk.Widget.set_border_width(n)` — maps to four `set_margin_*()` calls.
- `Gtk.Button.set_image(widget)` — wraps icon+label in a `Gtk.Box` child.
- `Gdk.Screen` — stub class, `.width()`/`.height()`/`.get_default()`
  delegated to `Gdk.Display.get_monitors()`.
- `Gtk.HButtonBox` — subclass of `Gtk.Box`, ignores `ButtonBoxStyle`.

### When to use the shim vs. port directly

Use the shim for:
- Mechanical call sites that would be identical search-and-replace otherwise.
- Third-party or Sugar-extension code you don't want to deeply modify.
- Large files with 20+ occurrences of `pack_start` — shimming once is less
  risky than spot-editing every call.

Port directly when:
- The surrounding code already needs a rewrite for other reasons.
- You're touching a leaf module with only 2-3 call sites (just fix them).
- The shim adds overhead you can measure (unlikely, but possible in tight
  animation loops).
- You're writing new code — never add new `pack_start` calls, even with
  the shim present.

## Container/Box API differences

The biggest conceptual change: GTK3's `Gtk.Container` subclass hierarchy
is gone. In GTK4, every widget can have ONE child (`set_child()` /
`get_child()`) or use a layout manager. Multi-child containers implement
their own child-tracking.

### Adding children

```python
# GTK3: any container, any number
box.pack_start(widget1, True, True, 0)
box.pack_start(widget2, False, False, 4)
box.pack_end(widget3, True, True, 0)

# GTK4: specific to widget type
box.append(widget1)   # Gtk.Box
box.append(widget2)   # Gtk.Box
box.prepend(widget3)  # Gtk.Box (replaces pack_end)
grid.attach(widget, col, row, w, h)  # Gtk.Grid (unchanged)
stack.add_titled(child, "name", "Title")  # Gtk.Stack (unchanged)
window.set_child(widget)  # single-child only
```

### Spacing and expand behavior

```python
# GTK3: spacing on the container, expand on pack
box = Gtk.HBox(spacing=6)
box.pack_start(widget, expand=True, fill=True, padding=4)

# GTK4: spacing on the container, expand on the CHILD widget
box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
widget.set_hexpand(True)
widget.set_vexpand(True)
widget.set_margin_start(4)
box.append(widget)
```

### Gtk.Container protocol → Gtk.LayoutManager

Custom containers that implemented `do_realize()`, `do_size_allocate()`,
`do_forall()` etc. in GTK3 must be ported to `Gtk.LayoutManager` subclasses
in GTK4:

```python
# GTK3: subclass Gtk.Container, implement do_size_allocate
class SnowflakeLayout(Gtk.Container):
    def do_size_allocate(self, allocation):
        for child, pos in enumerate(self._positions):
            child_alloc = Gdk.Rectangle()
            child_alloc.width = child.get_preferred_width()[0]
            child_alloc.height = child.get_preferred_height()[0]
            child_alloc.x = allocation.x + pos.x
            child_alloc.y = allocation.y + pos.y
            child.size_allocate(child_alloc)

# GTK4: subclass Gtk.LayoutManager, implement allocate
class SnowflakeLayout(Gtk.LayoutManager):
    def do_allocate(self, widget, width, height, baseline):
        for child, pos in zip(self._children, self._positions):
            child_w = child.get_preferred_width()
            child_h = child.get_preferred_height()
            child.allocate(pos.x, pos.y, child_w, child_h, None)
```

This is the hardest migration path in GTK4 — Sugar's `SnowflakeLayout` and
`ViewContainer` are currently stubbed to plain `Gtk.Box` packing (see
[[gtk-porting-standards]]). Real porting of these requires implementing
full `Gtk.LayoutManager` subclasses with `do_get_request_mode()`,
`do_measure()`, and `do_allocate()`.

## Event controllers vs signal handlers

GTK3 used "event" signals on widgets (`"button-press-event"`,
`"motion-notify-event"`). GTK4 replaces these with event controllers:

```python
# GTK3:
widget.connect("button-press-event", self._on_press)
def _on_press(self, widget, event):
    print(f"Pressed at {event.x}, {event.y}, button {event.button}")

# GTK4:
click = Gtk.GestureClick.new()
click.connect("pressed", self._on_press)
widget.add_controller(click)

def _on_press(self, gesture, n_press, x, y):
    button = gesture.get_current_button()
    print(f"Pressed at {x}, {y}, button {button}")
```

### Common event controller replacements

| GTK3 signal | GTK4 controller |
|-------------|-----------------|
| `"button-press-event"` | `Gtk.GestureClick` |
| `"button-release-event"` | `Gtk.GestureClick` (signal: `"released"`) |
| `"motion-notify-event"` | `Gtk.EventControllerMotion` |
| `"key-press-event"` | `Gtk.EventControllerKey` |
| `"key-release-event"` | `Gtk.EventControllerKey` (signal: `"key-released"`) |
| `"scroll-event"` | `Gtk.EventControllerScroll` |
| `"enter-notify-event"` / `"leave-notify-event"` | `Gtk.EventControllerMotion` (signals: `"enter"` / `"leave"`) |
| `"touch-event"` | `Gtk.Gesture` subclasses (LongPress, Swipe, Rotate, Zoom) |
| `"draw"` | `Gtk.Widget.set_draw_func()` (see below) |

### Controller lifecycle

Controllers must be added to a widget before they fire. They are
automatically disposed when the widget is destroyed — no manual cleanup
needed for widget-bound controllers. For global or multi-widget
controllers, `Gtk.EventController` is not meant for that — use
`Gtk.EventControllerKey` with `set_propagation_phase(Gtk.PropagationPhase.CAPTURE)` on a toplevel, or handle events in the widget tree.

## Drawing model changes (snapshot vs draw)

GTK3's `"draw"` signal gave you a `cairo.Context`. GTK4 replaces this
with `Gtk.Snapshot` and render nodes:

```python
# GTK3:
widget.connect("draw", self._on_draw)
def _on_draw(self, widget, cr):
    cr.set_source_rgb(1, 0, 0)
    cr.rectangle(10, 10, 100, 50)
    cr.fill()

# GTK4:
widget.set_draw_func(self._on_draw)
def _on_draw(self, widget, snapshot, width, height):
    color = Gdk.RGBA()
    color.parse("#ff0000")
    snapshot.append_color(color, Gsk.RoundedRect())
    # Or for more complex drawing, use cairo through a render node:
    # cr = snapshot.append_cairo(Graphene.Rect().__init__(0, 0, width, height))
    # cr.set_source_rgb(1, 0, 0)
    # cr.rectangle(10, 10, 100, 50)
    # cr.fill()
```

Key differences:
- `set_draw_func()` is set once, not connected as a signal.
- `Gtk.Snapshot` is append-only — you add render nodes in z-order.
- For Cairo-based drawing (porting old `cairo.Context` code),
  `snapshot.append_cairo()` still works and creates a `cairo` node.
- CSS-drawn widgets (`Gtk.Box` backgrounds, borders, shadows) are
  handled by GTK's CSS engine — no need to draw them manually.

## Custom widget sizing

```python
# GTK3: get_preferred_width / get_preferred_height virtual methods
class MyWidget(Gtk.Widget):
    def do_get_preferred_width(self):
        return (100, 200)  # minimum, natural

# GTK4: measure() vfunc
class MyWidget(Gtk.Widget):
    def do_measure(self, orientation, for_size):
        if orientation == Gtk.Orientation.HORIZONTAL:
            return (100, 200, -1, -1)  # min, natural, min_baseline, nat_baseline
        else:
            return (50, 100, -1, -1)
```

## Gtk.Application boilerplate

GTK4's Application API is largely identical to GTK3's, but some defaults
changed:

```python
# GTK3:
app = Gtk.Application(application_id="org.example.MyApp")
# GTK4:
app = Gtk.Application(application_id="org.example.MyApp",
                      flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
```

GTK4 applications auto-load menus from `GMenu` via `Gtk.Application.set_menubar()` or `set_accels_for_action()`. The XML-based `Gtk.Builder` menu system is unchanged.

## Notes

- The `sugar4/gtk3compat.py` shim is a development aid, not a permanent
  solution. All new code should use GTK4 APIs directly. The shim exists
  to get jarabe running while the real migration continues.
- GI (GObject Introspection) in GTK4 requires **keyword arguments** for
  all constructors. `Gtk.Button("label")` is a GI error in GTK4 — must
  be `Gtk.Button(label="label")`. The shim does not paper over this.
- Some GTK3 widgets have no direct GTK4 equivalent:
  - `Gtk.TreeView` + `Gtk.ListStore` → `Gtk.ColumnView` + `Gio.ListStore`
    (model/view separation, different API entirely).
  - `Gtk.Notebook` → `Gtk.Stack` + `Gtk.StackSwitcher` (still available
    as `Gtk.Notebook` in GTK4 but deprecated, use `Gtk.Stack`).
  - `Gtk.FileChooserDialog` → `Gtk.FileDialog` (async API).
- Event controllers do NOT support connecting with user data args (the
  `*args` in `connect("signal", handler, user_data1, user_data2)`
  pattern). Use closures or `functools.partial` instead:

```python
# GTK3:
widget.connect("button-press-event", self._on_press, "data")

# GTK4:
gesture.connect("pressed", lambda g, n, x, y: self._on_press("data", x, y))
```
