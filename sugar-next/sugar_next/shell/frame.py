"""Sugar Next Frame — top-edge overlay with favorites and running apps.

Revealed by the top-right hot corner or F6 (Sugar's classic frame key).
v0 shows pinned favorites plus apps launched this session; universal
window listing needs compositor support and is future work (see the
sugar-next design doc).
"""

import json
import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio


def _favorites_file() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return Path(data_home) / "sugar-next" / "favorites.json"


class _FrameItem(Gtk.Box):
    """Icon in the frame bar. Click launches; right-click opens a palette."""

    def __init__(self, bundle, palette_actions):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.bundle = bundle
        self.set_tooltip_text(bundle.name)

        button = Gtk.Button()
        button.add_css_class("flat")
        icon = bundle.icon
        image = (
            Gtk.Image.new_from_gicon(icon)
            if icon
            else Gtk.Image.new_from_icon_name("application-x-executable")
        )
        image.set_pixel_size(32)
        button.set_child(image)
        button.connect("clicked", lambda *_: bundle.launch())
        self.append(button)

        self._palette = Gtk.Popover()
        self._palette.set_parent(button)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title = Gtk.Label(label=bundle.name)
        title.add_css_class("heading")
        box.append(title)
        for label, callback in palette_actions:
            action_button = Gtk.Button(label=label)
            action_button.add_css_class("flat")
            if callback is None:
                action_button.set_sensitive(False)
            else:
                action_button.connect(
                    "clicked", self._on_palette_action, callback
                )
            box.append(action_button)
        self._palette.set_child(box)

        right_click = Gtk.GestureClick()
        right_click.set_button(3)
        right_click.connect("pressed", lambda *_: self._palette.popup())
        button.add_controller(right_click)

    def _on_palette_action(self, button, callback):
        self._palette.popdown()
        callback(self.bundle)


class SugarFrame(Gtk.Revealer):
    __gtype_name__ = "SugarNextFrame"

    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.FILL)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.add_css_class("frame-bar")
        bar.set_margin_start(8)
        bar.set_margin_end(8)
        bar.set_margin_top(4)
        bar.set_margin_bottom(4)
        self.set_child(bar)

        self._favorites_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4
        )
        bar.append(self._favorites_box)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self._running_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4
        )
        bar.append(self._running_box)

        self._favorite_ids = self._load_favorites()
        self._running_ids = set()
        self._rebuild_favorites()

    def toggle(self):
        self.set_reveal_child(not self.get_reveal_child())

    def reveal(self):
        self.set_reveal_child(True)

    # -- favorites ---------------------------------------------------------

    def pin_favorite(self, bundle):
        if bundle.app_id in self._favorite_ids:
            return
        self._favorite_ids.append(bundle.app_id)
        self._save_favorites()
        self._rebuild_favorites()

    def _unpin_favorite(self, bundle):
        if bundle.app_id in self._favorite_ids:
            self._favorite_ids.remove(bundle.app_id)
            self._save_favorites()
            self._rebuild_favorites()

    def _rebuild_favorites(self):
        from sugar_next.bundles.desktop_bundle import DesktopBundle

        while child := self._favorites_box.get_first_child():
            self._favorites_box.remove(child)
        for app_id in self._favorite_ids:
            try:
                app_info = Gio.DesktopAppInfo.new(app_id)
            except TypeError:
                # App uninstalled since it was pinned.
                app_info = None
            if app_info is None:
                continue
            bundle = DesktopBundle(app_info)
            item = _FrameItem(
                bundle,
                palette_actions=[
                    ("Unpin from favorites", self._unpin_favorite),
                    ("Add to Journal (coming soon)", None),
                ],
            )
            self._favorites_box.append(item)

    def _load_favorites(self):
        path = _favorites_file()
        if path.is_file():
            try:
                return list(json.loads(path.read_text()))
            except ValueError:
                pass
        return []

    def _save_favorites(self):
        path = _favorites_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._favorite_ids, indent=2))

    # -- running apps ------------------------------------------------------

    def add_running(self, bundle):
        """Track an app launched this session and show it in the frame."""
        if bundle.app_id in self._running_ids:
            return
        self._running_ids.add(bundle.app_id)
        item = _FrameItem(
            bundle,
            palette_actions=[
                ("Pin to favorites", self.pin_favorite),
                ("Add to Journal (coming soon)", None),
            ],
        )
        self._running_box.append(item)
