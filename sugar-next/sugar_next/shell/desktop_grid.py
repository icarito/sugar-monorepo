"""Desktop grid Home View layout (Endless-inspired).

Icons float over a user-selectable background image. Apps are clustered
into category "container folders" that expand into a sub-grid; there is
no folder nesting beyond one level.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, Pango


_UNCATEGORIZED = "Apps"


class _IconCell(Gtk.Box):
    """A single floating icon: an app bundle or a container folder."""

    def __init__(self, icon_paintable_source, label_text, on_activate):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.CENTER)
        self.add_css_class("desktop-grid-cell")

        self.icon = icon_paintable_source
        if self.icon.get_pixel_size() <= 0:
            self.icon.set_pixel_size(48)
        self.append(self.icon)

        label = Gtk.Label(label=label_text)
        label.set_max_width_chars(12)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_justify(Gtk.Justification.CENTER)
        self.append(label)

        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_: on_activate())
        self.add_controller(click)


class SugarDesktopGrid(Gtk.Overlay):
    __gtype_name__ = "SugarNextDesktopGrid"

    view_id = "desktop-grid"
    view_name = "Desktop"

    _CSS = """
        .desktop-grid-cell {
            border-radius: 14px;
            padding: 10px;
            background: none;
            border: none;
            box-shadow: none;
            transition: all 150ms ease;
            min-width: 100px;
        }
        .desktop-grid-cell:hover {
            background: rgba(255,255,255,0.12);
        }
        .desktop-grid-cell:active {
            background: rgba(0,0,0,0.15);
        }
        .desktop-grid-cell label {
            color: white;
            text-shadow: 0 1px 3px rgba(0,0,0,0.7);
            font-size: 10pt;
        }
        .desktop-grid-folder label {
            color: #e0e0e0;
            text-shadow: 0 1px 3px rgba(0,0,0,0.7);
        }
    """

    def __init__(self, background_path=None):
        super().__init__()

        provider = Gtk.CssProvider()
        provider.load_from_string(self._CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # The desktop grid renders no wallpaper of its own: the shell-level
        # background picture and its brightness/contrast wash sit *behind*
        # every Home View layout, so this layout stays transparent and lets
        # that single, uniformly-adjusted background show through. (The
        # `set_background` method is kept as a no-op for API compatibility
        # with the shell and Settings panel, which still call it.)
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_vexpand(True)
        self._stack.set_hexpand(True)
        self.set_child(self._stack)

        self._root_flow = self._make_flow_box()
        self._stack.add_named(self._root_flow, "root")
        self._folder_flows = {}

        self._on_launch = None
        self._all_cells = []
        self._bundles = []
        self._icon_size = 48

    def set_background(self, path):
        # No-op: the shell owns the wallpaper (see __init__). Kept so the
        # shell/Settings panel can call it uniformly across layouts.
        pass

    def set_on_launch(self, callback):
        self._on_launch = callback

    def set_icon_size(self, icon_size):
        self._icon_size = icon_size
        self.populate(self._bundles)

    def _make_flow_box(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        flow_box = Gtk.FlowBox()
        flow_box.set_valign(Gtk.Align.FILL)
        flow_box.set_halign(Gtk.Align.FILL)
        flow_box.set_max_children_per_line(10)
        flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        flow_box.set_margin_start(24)
        flow_box.set_margin_end(24)
        flow_box.set_margin_top(24)
        flow_box.set_margin_bottom(24)
        scrolled.set_child(flow_box)
        scrolled.flow_box = flow_box
        return scrolled

    def populate(self, bundles):
        """Group bundles by category into container folders."""
        self._bundles = list(bundles)
        while child := self._root_flow.flow_box.get_first_child():
            self._root_flow.flow_box.remove(child)
        self._folder_flows.clear()

        groups = {}
        for bundle in bundles:
            category = getattr(bundle, "category", None) or _UNCATEGORIZED
            groups.setdefault(category, []).append(bundle)

        for category, members in sorted(groups.items()):
            if len(members) == 1:
                self._add_app_cell(self._root_flow.flow_box, members[0])
            else:
                self._add_folder_cell(category, members)

    def _add_app_cell(self, flow_box, bundle):
        icon = bundle.icon
        image = (
            Gtk.Image.new_from_gicon(icon)
            if icon
            else Gtk.Image.new_from_icon_name("application-x-executable")
        )
        image.set_pixel_size(self._icon_size)
        cell = _IconCell(image, bundle.name, lambda: self._launch(bundle))
        flow_box.append(cell)

    def _launch(self, bundle):
        bundle.launch()
        if self._on_launch is not None:
            self._on_launch(bundle)

    def _add_folder_cell(self, category, members):
        image = Gtk.Image.new_from_icon_name("folder")
        image.set_pixel_size(self._icon_size)
        cell = _IconCell(
            image, category, lambda: self._open_folder(category, members)
        )
        cell.add_css_class("desktop-grid-folder")
        self._root_flow.flow_box.append(cell)

    def _open_folder(self, category, members):
        if category not in self._folder_flows:
            sub_flow = self._make_flow_box()
            back = Gtk.Button(label=f"← {category}")
            back.add_css_class("flat")
            back.connect("clicked", lambda *_: self._stack.set_visible_child_name("root"))
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            box.append(back)
            box.append(sub_flow)
            for bundle in members:
                self._add_app_cell(sub_flow.flow_box, bundle)
            self._stack.add_named(box, f"folder:{category}")
            self._folder_flows[category] = box
        self._stack.set_visible_child_name(f"folder:{category}")

    def on_activate(self):
        pass

    def on_deactivate(self):
        # Preserve the open folder across view switches (frame-views spec).
        pass
