import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, Gio, GLib, Pango



class _AppGridCell(Gtk.Box):
    __gtype_name__ = "SugarNextAppGridCell"

    def __init__(self, bundle, on_launched=None, on_pin=None, icon_size=48):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.bundle = bundle
        self._on_launched = on_launched
        self._on_pin = on_pin
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.add_css_class("app-grid-cell")

        icon_info = bundle.icon
        if icon_info:
            self.icon = Gtk.Image.new_from_gicon(icon_info)
        else:
            self.icon = Gtk.Image.new_from_icon_name("application-x-executable")
        self.icon.set_pixel_size(icon_size)
        self.append(self.icon)

        self.label = Gtk.Label(label=bundle.name)
        self.label.set_max_width_chars(12)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.append(self.label)

        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        self.add_controller(click)

        if on_pin is not None:
            right_click = Gtk.GestureClick()
            right_click.set_button(3)
            right_click.connect("pressed", self._on_right_click)
            self.add_controller(right_click)

    def _on_pressed(self, gesture, n_press, x, y):
        self.bundle.launch()
        if self._on_launched is not None:
            self._on_launched(self.bundle)

    def _on_right_click(self, gesture, n_press, x, y):
        popover = Gtk.Popover()
        popover.set_parent(self)
        pin_button = Gtk.Button(label="Pin to Frame favorites")
        pin_button.add_css_class("flat")

        def _pin(_button):
            popover.popdown()
            self._on_pin(self.bundle)

        pin_button.connect("clicked", _pin)
        popover.set_child(pin_button)
        popover.popup()


class SugarAppGrid(Gtk.Box):
    __gtype_name__ = "SugarNextAppGrid"

    view_id = "app-grid"
    view_name = "Apps"

    _CSS = """
        .app-grid-cell {
            border-radius: 14px;
            padding: 10px;
            background: none;
            border: none;
            box-shadow: none;
            transition: all 150ms ease;
        }
        .app-grid-cell:hover {
            background: linear-gradient(180deg,
                rgba(128,128,128,0.10) 0%,
                rgba(128,128,128,0.04) 100%
            );
        }
        .app-grid-cell:active {
            background: linear-gradient(180deg,
                rgba(128,128,128,0.15) 0%,
                rgba(128,128,128,0.08) 100%
            );
        }
        .app-grid-cell label {
            color: var(--sn-text);
            font-size: 11pt;
        }
    """

    def __init__(self, on_launched=None, on_pin=None, icon_size=48):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_launched = on_launched
        self._on_pin = on_pin
        self._icon_size = icon_size

        provider = Gtk.CssProvider()
        provider.load_from_string(self._CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search applications...")
        self._search_entry.set_margin_start(16)
        self._search_entry.set_margin_end(16)
        self._search_entry.set_margin_top(8)
        self._search_entry.set_margin_bottom(8)
        self._search_entry.connect("search-changed", self._on_search_changed)
        self.append(self._search_entry)

        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self._scrolled.set_vexpand(True)
        self.append(self._scrolled)

        self._flow_box = Gtk.FlowBox()
        self._flow_box.set_valign(Gtk.Align.START)
        self._flow_box.set_max_children_per_line(8)
        self._flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._flow_box.set_row_spacing(4)
        self._flow_box.set_column_spacing(4)
        self._flow_box.set_margin_start(16)
        self._flow_box.set_margin_end(16)
        self._flow_box.set_margin_top(8)
        self._flow_box.set_margin_bottom(16)
        self._flow_box.set_filter_func(self._filter_func)
        self._scrolled.set_child(self._flow_box)

        self._all_cells = []

        self._populate()

    def _populate(self):
        bundles = self._load_bundles()
        for bundle in bundles:
            cell = _AppGridCell(
                bundle,
                on_launched=self._on_launched,
                on_pin=self._on_pin,
                icon_size=self._icon_size,
            )
            self._all_cells.append(cell)
            self._flow_box.append(cell)

    def _load_bundles(self):
        from sugar_next.bundles.desktop_bundle import DesktopBundle

        return DesktopBundle.sorted_apps()

    def set_icon_size(self, icon_size):
        self._icon_size = icon_size
        while child := self._flow_box.get_first_child():
            self._flow_box.remove(child)
        self._all_cells = []
        self._populate()

    def _on_search_changed(self, entry):
        self._flow_box.invalidate_filter()

    def on_activate(self):
        pass

    def on_deactivate(self):
        # Views preserve their own state (search text, scroll position)
        # across switches — see the frame-views spec. Nothing is reset.
        pass

    def _filter_func(self, child):
        # FlowBox wraps each cell in a Gtk.FlowBoxChild.
        if child is None:
            return False
        text = self._search_entry.get_text()
        if not text:
            return True
        cell = child.get_child() if isinstance(child, Gtk.FlowBoxChild) else child
        if hasattr(cell, "bundle"):
            return text.lower() in cell.bundle.name.lower()
        return False
