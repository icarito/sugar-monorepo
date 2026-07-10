"""Desktop pie menu — radial layout of pinned favorites.

Replaces the Desktop grid: a personal, minimal space showing only the
learner's pinned favorites, arranged in a circle around the view center.
The circle's center button opens Settings (see the desktop-pie-menu
design doc — Settings moves out of the Frame into the pie menu).
"""

import json
import math
import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk


def _favorites_file() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return Path(data_home) / "sugar-next" / "favorites.json"


class _Petal(Gtk.Button):
    """One favorite, positioned on the circle via Gtk.Fixed coordinates."""

    def __init__(self, bundle, on_activate, on_unpin, icon_size=48):
        super().__init__()
        self.bundle = bundle
        self.add_css_class("flat")
        self.add_css_class("pie-menu-petal")
        self.set_tooltip_text(bundle.name)

        icon = bundle.icon
        image = (
            Gtk.Image.new_from_gicon(icon)
            if icon
            else Gtk.Image.new_from_icon_name("application-x-executable")
        )
        image.set_pixel_size(icon_size)
        self.set_child(image)

        self.connect("clicked", lambda *_: on_activate(bundle))

        right_click = Gtk.GestureClick()
        right_click.set_button(3)
        right_click.connect("pressed", lambda *_a: on_unpin(bundle))
        self.add_controller(right_click)


class SugarPieMenu(Gtk.Fixed):
    """Desktop view: pinned favorites arranged radially, center → Settings."""

    __gtype_name__ = "SugarNextPieMenu"

    view_id = "desktop-grid"
    view_name = "Desktop"

    _CSS = """
        .pie-menu-petal {
            border-radius: 50%;
            padding: 8px;
            background: rgba(0,0,0,0.25);
            transition: opacity 200ms ease, background 150ms ease;
        }
        .pie-menu-petal:hover {
            background: rgba(255,255,255,0.20);
        }
        .pie-menu-center {
            border-radius: 50%;
            min-width: 56px;
            min-height: 56px;
            background: rgba(0,0,0,0.35);
        }
        .pie-menu-center:hover {
            background: var(--sn-accent);
        }
        .pie-menu-empty-label {
            color: white;
            text-shadow: 0 1px 3px rgba(0,0,0,0.7);
        }
    """

    #: Radius (px) of the circle the petals sit on.
    _RADIUS = 140

    def __init__(self, on_settings=None, icon_size=48):
        super().__init__()
        # Without expand, a Gtk.Fixed shrinks to its content's natural
        # size — with no petals, that's just the center button, so the
        # widget (and the "center" the button is placed at) collapses to
        # a tiny box instead of filling the view. Expanding keeps it the
        # full view size regardless of favorite count.
        self.set_hexpand(True)
        self.set_vexpand(True)
        self._on_settings = on_settings
        self._icon_size = icon_size
        self._favorite_ids = self._load_favorites()
        self._petals = []

        provider = Gtk.CssProvider()
        provider.load_from_string(self._CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self._empty_label = Gtk.Label(
            label="Pin apps from the Apps view to see them here"
        )
        self._empty_label.add_css_class("pie-menu-empty-label")
        self._empty_label.set_visible(False)
        self.put(self._empty_label, 0, 0)

        self._center_button = Gtk.Button()
        self._center_button.add_css_class("pie-menu-center")
        self._center_button.set_icon_name("emblem-system-symbolic")
        self._center_button.connect("clicked", self._on_center_clicked)
        self.put(self._center_button, 0, 0)

        self._rebuild()

    def do_size_allocate(self, width, height, baseline):
        Gtk.Fixed.do_size_allocate(self, width, height, baseline)
        self._reflow(width, height)

    # -- layout --------------------------------------------------------

    def _reflow(self, width=None, height=None):
        if width is None:
            width = self.get_width()
        if height is None:
            height = self.get_height()
        if width <= 0 or height <= 0:
            return
        cx, cy = width / 2, height / 2

        center_w = self._center_button.get_width() or 56
        center_h = self._center_button.get_height() or 56
        self.move(self._center_button, cx - center_w / 2, cy - center_h / 2)

        label_w = self._empty_label.get_width() or 0
        label_h = self._empty_label.get_height() or 0
        self.move(self._empty_label, cx - label_w / 2, cy + 60 - label_h / 2)

        count = len(self._petals)
        if count == 0:
            return
        step = 2 * math.pi / count
        for index, petal in enumerate(self._petals):
            angle = -math.pi / 2 + index * step
            petal_w = petal.get_width() or 56
            petal_h = petal.get_height() or 56
            x = cx + self._RADIUS * math.cos(angle) - petal_w / 2
            y = cy + self._RADIUS * math.sin(angle) - petal_h / 2
            self.move(petal, x, y)

    # -- favorites -------------------------------------------------------

    def _load_favorites(self):
        path = _favorites_file()
        if path.is_file():
            try:
                return list(json.loads(path.read_text()))
            except ValueError:
                pass
        return []

    def refresh_favorites(self):
        """Reload favorites.json and rebuild petals (e.g. pinned elsewhere)."""
        self._favorite_ids = self._load_favorites()
        self._rebuild()

    def pin_favorite(self, bundle):
        """Pin *bundle* as a favorite (called from the Apps view)."""
        if bundle.app_id in self._favorite_ids:
            return
        self._favorite_ids.append(bundle.app_id)
        self._save_favorites()
        self._rebuild()

    def _rebuild(self):
        from sugar_next.bundles.desktop_bundle import DesktopBundle

        for petal in self._petals:
            self.remove(petal)
        self._petals = []

        for app_id in self._favorite_ids:
            try:
                app_info = Gio.DesktopAppInfo.new(app_id)
            except TypeError:
                app_info = None
            if app_info is None:
                continue
            bundle = DesktopBundle(app_info)
            petal = _Petal(
                bundle,
                on_activate=self._launch,
                on_unpin=self._unpin,
                icon_size=self._icon_size,
            )
            self.put(petal, 0, 0)
            self._petals.append(petal)

        self._empty_label.set_visible(len(self._petals) == 0)
        self._reflow()
        self._animate_reveal()

    def _animate_reveal(self):
        # Petals start transparent; opacity is flipped to 1 on the next
        # idle pass once positioned, giving a soft fade-in reveal instead
        # of popping in at full opacity immediately.
        for petal in self._petals:
            petal.set_opacity(0.0)

        def _fade():
            for petal in self._petals:
                petal.set_opacity(1.0)
            return False

        GLib.idle_add(_fade)

    def _launch(self, bundle):
        bundle.launch()

    def _unpin(self, bundle):
        if bundle.app_id in self._favorite_ids:
            self._favorite_ids.remove(bundle.app_id)
            self._save_favorites()
            self._rebuild()

    def _save_favorites(self):
        path = _favorites_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._favorite_ids, indent=2))

    def _on_center_clicked(self, _button):
        if self._on_settings is not None:
            self._on_settings()

    # -- Home View / shell API -------------------------------------------

    def set_background(self, path):
        # No-op: the shell owns the wallpaper, same as the old desktop_grid.
        pass

    def set_icon_size(self, icon_size):
        self._icon_size = icon_size
        self._rebuild()

    def on_activate(self):
        # Pick up favorites pinned from the Apps view since last shown.
        self.refresh_favorites()

    def on_deactivate(self):
        pass
