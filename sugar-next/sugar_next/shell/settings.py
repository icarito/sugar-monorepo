"""Settings panel.

Accessible from the Frame or a keybinding. Every control here belongs to
the learner: background, accent, contrast, icon size, Home View layout,
and installed extensions. There is no deployment-level override for any
of these — see sugar-next/HIG.md, "The Home View is yours".
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk

from sugar_next.api.hooks import list_extensions, registry, set_extension_enabled
from sugar_next.shell.settings_store import SettingsStore, icon_size_px
from sugar_next.shell.theme import DEFAULT_ACCENT, manager as theme_manager

_ACCENT_PRESETS = [
    "#3584e4",  # blue
    "#33d17a",  # green
    "#f6d32d",  # yellow
    "#ff7800",  # orange
    "#e01b24",  # red
    "#9141ac",  # purple
    "#1a5fb4",  # dark blue
    "#26a269",  # dark green
]

_KEYBINDINGS = [
    ("F1 / F10", "Open/close Settings"),
    ("F6", "Toggle the Frame"),
    ("Search", "Type to filter apps (App Grid / Search First)"),
    ("Esc", "Close popover, return to Home"),
]


class SettingsPanel(Gtk.Popover):
    __gtype_name__ = "SugarNextSettingsPanel"

    def __init__(self, home_view=None, store=None, shell=None):
        super().__init__()
        self.set_autohide(True)
        self.set_has_arrow(False)
        self._home_view = home_view
        self._store = store or SettingsStore()
        self._shell = shell

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_max_content_height(520)
        scrolled.set_propagate_natural_height(True)
        self.set_child(scrolled)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_size_request(320, -1)
        scrolled.set_child(box)

        box.append(self._build_background_row())
        box.append(self._build_accent_row())
        box.append(self._build_contrast_row())
        box.append(self._build_icon_size_row())
        if self._home_view is not None:
            box.append(self._build_layout_row())
        box.append(self._build_extensions_row())
        box.append(self._build_keybindings_row())
        box.append(self._build_about_row())

    # -- background ----------------------------------------------------

    def _build_background_row(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.append(Gtk.Label(label="Background", xalign=0, hexpand=True))
        self._bg_label = Gtk.Label(
            label="None", xalign=1, hexpand=False,
            ellipsize=3, max_width_chars=20,
        )
        row.append(self._bg_label)
        button = Gtk.Button(label="Choose image\u2026")
        button.connect("clicked", self._on_choose_background)
        row.append(button)
        clear_btn = Gtk.Button(label="Clear")
        clear_btn.add_css_class("flat")
        clear_btn.connect("clicked", self._on_clear_background)
        row.append(clear_btn)
        return row

    def _on_choose_background(self, _button):
        dialog = Gtk.FileChooserNative.new(
            "Choose a background image",
            self.get_root(),
            Gtk.FileChooserAction.OPEN,
            "Select",
            "Cancel",
        )
        dialog.connect("response", self._on_background_chosen)
        dialog.show()
        self._background_dialog = dialog

    def _on_background_chosen(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file is not None:
                path = file.get_path()
                self._store.set("background_path", path)
                self._bg_label.set_label(file.get_basename() or "Image")
                if self._shell is not None and hasattr(self._shell, "set_background"):
                    self._shell.set_background(path)
                if self._home_view is not None:
                    desktop_grid = self._home_view_layout("desktop-grid")
                    if desktop_grid is not None and hasattr(
                        desktop_grid, "set_background"
                    ):
                        desktop_grid.set_background(path)
        dialog.destroy()

    def _on_clear_background(self, _button):
        self._store.set("background_path", "")
        self._bg_label.set_label("None")
        if self._shell is not None and hasattr(self._shell, "set_background"):
            self._shell.set_background(None)
        if self._home_view is not None:
            desktop_grid = self._home_view_layout("desktop-grid")
            if desktop_grid is not None and hasattr(desktop_grid, "set_background"):
                desktop_grid.set_background(None)

    # -- accent ----------------------------------------------------------

    def _build_accent_row(self):
        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.append(Gtk.Label(label="Accent color", xalign=0, hexpand=True))
        current_color = self._store.get("accent_color")
        self._accent_label = Gtk.Label(
            label=current_color or DEFAULT_ACCENT,
            xalign=1, hexpand=False,
        )
        header.append(self._accent_label)
        column.append(header)

        presets_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        presets_row.set_homogeneous(True)
        css_rules = []
        for index, hex_color in enumerate(_ACCENT_PRESETS):
            swatch = Gtk.Button()
            swatch.add_css_class("circular")
            swatch.add_css_class(f"sn-swatch-{index}")
            swatch.set_size_request(24, 24)
            css_rules.append(
                f".sn-swatch-{index} {{ background: {hex_color};"
                " min-width: 24px; min-height: 24px; border: 2px solid"
                " transparent; }"
                f".sn-swatch-{index}:hover {{ border-color: white; }}"
            )
            swatch.connect("clicked", self._on_accent_chosen, hex_color)
            presets_row.append(swatch)
        provider = Gtk.CssProvider()
        provider.load_from_string("\n".join(css_rules))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        column.append(presets_row)

        custom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._custom_accent_entry = Gtk.Entry()
        self._custom_accent_entry.set_placeholder_text("#rrggbb")
        self._custom_accent_entry.set_max_length(7)
        self._custom_accent_entry.set_hexpand(True)
        custom_row.append(self._custom_accent_entry)
        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self._on_custom_accent_apply)
        custom_row.append(apply_button)
        column.append(custom_row)

        return column

    def _on_accent_chosen(self, _button, hex_color):
        self._store.set("accent_color", hex_color)
        self._accent_label.set_label(hex_color)
        theme_manager.set_accent_tint(hex_color)

    def _on_custom_accent_apply(self, _button):
        text = self._custom_accent_entry.get_text().strip()
        if len(text) == 7 and text.startswith("#"):
            self._on_accent_chosen(None, text)

    # -- contrast ----------------------------------------------------------

    def _build_contrast_row(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.append(Gtk.Label(label="High contrast", xalign=0, hexpand=True))
        switch = Gtk.Switch()
        switch.set_active(self._store.get("contrast") == "high")
        switch.connect("state-set", self._on_contrast_toggled)
        row.append(switch)
        return row

    def _on_contrast_toggled(self, _switch, state):
        level = "high" if state else "normal"
        self._store.set("contrast", level)
        theme_manager.set_contrast(level)
        return False

    # -- icon size ----------------------------------------------------------

    def _build_icon_size_row(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.append(Gtk.Label(label="Icon size", xalign=0, hexpand=True))
        dropdown = Gtk.DropDown.new_from_strings(["small", "medium", "large"])
        sizes = ["small", "medium", "large"]
        current = self._store.get("icon_size")
        if current in sizes:
            dropdown.set_selected(sizes.index(current))
        dropdown.connect("notify::selected", self._on_icon_size_changed, sizes)
        row.append(dropdown)
        return row

    def _on_icon_size_changed(self, dropdown, _pspec, sizes):
        size_name = sizes[dropdown.get_selected()]
        self._store.set("icon_size", size_name)
        if self._home_view is not None:
            px = icon_size_px(size_name)
            for layout_id in self._home_view.layout_ids():
                layout = self._home_view_layout(layout_id)
                if layout is not None and hasattr(layout, "set_icon_size"):
                    layout.set_icon_size(px)

    # -- home view layout ----------------------------------------------------------

    def _build_layout_row(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.append(Gtk.Label(label="Home View layout", xalign=0, hexpand=True))
        layout_ids = self._home_view.layout_ids()
        dropdown = Gtk.DropDown.new_from_strings(layout_ids)
        if self._home_view.active_id in layout_ids:
            dropdown.set_selected(layout_ids.index(self._home_view.active_id))
        dropdown.connect("notify::selected", self._on_layout_changed, layout_ids)
        row.append(dropdown)
        return row

    def _on_layout_changed(self, dropdown, _pspec, layout_ids):
        layout_id = layout_ids[dropdown.get_selected()]
        self._store.set("home_view_layout", layout_id)
        self._home_view.set_active(layout_id)

    def _home_view_layout(self, layout_id):
        if self._home_view is None:
            return None
        return self._home_view._layouts.get(layout_id)

    # -- extensions ----------------------------------------------------------

    def _build_extensions_row(self):
        self._extensions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._extensions_box.append(Gtk.Label(label="Extensions", xalign=0))
        self._rebuild_extensions_list()
        return self._extensions_box

    def _rebuild_extensions_list(self):
        child = self._extensions_box.get_first_child()
        if child is not None:
            child = child.get_next_sibling()
        while child is not None:
            next_child = child.get_next_sibling()
            self._extensions_box.remove(child)
            child = next_child

        extensions = list_extensions()
        if not extensions:
            self._extensions_box.append(
                Gtk.Label(label="(none installed)", xalign=0)
            )
            return
        for name, enabled in extensions:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.append(Gtk.Label(label=name, xalign=0, hexpand=True))
            switch = Gtk.Switch()
            switch.set_active(enabled)
            switch.connect("state-set", self._on_extension_toggled, name)
            row.append(switch)
            self._extensions_box.append(row)

    def _on_extension_toggled(self, _switch, state, name):
        set_extension_enabled(name, state)
        registry.load()
        return False

    # -- keybindings ----------------------------------------------------------

    def _build_keybindings_row(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.append(Gtk.Label(label="Keybindings", xalign=0))
        for key, description in _KEYBINDINGS:
            box.append(Gtk.Label(label=f"{key} \u2014 {description}", xalign=0))
        return box

    # -- about ----------------------------------------------------------

    def _build_about_row(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.append(Gtk.Label(label="Sugar Next", xalign=0))
        box.append(
            Gtk.Label(label="A Learning Shell for Everyday Computing", xalign=0)
        )
        box.append(Gtk.Label(label="GPL-3.0-or-later", xalign=0))
        return box
