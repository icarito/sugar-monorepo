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
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, Gio


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

        provider = Gtk.CssProvider()
        provider.load_from_string(
            """
            .frame-bar {
                background-color: var(--sn-bg-alt);
                border-top: 2px solid var(--sn-accent);
                border-radius: 0 0 12px 12px;
                padding: 8px 16px;
                min-height: 48px;
                transition: border-color 400ms ease;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.add_css_class("frame-bar")
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

        self._settings_button = Gtk.MenuButton()
        self._settings_button.add_css_class("flat")
        self._settings_button.set_icon_name("emblem-system-symbolic")
        self._settings_button.set_hexpand(True)
        self._settings_button.set_halign(Gtk.Align.END)
        bar.append(self._settings_button)

        self._favorite_ids = self._load_favorites()
        self._running_ids = set()
        self._rebuild_favorites()

    @property
    def settings_button(self):
        return self._settings_button

    def set_settings_panel(self, popover):
        self._settings_button.set_popover(popover)

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
        item.app_id = bundle.app_id
        self._running_box.append(item)

    def remove_running(self, app_id, app_info=None):
        """Stop showing an app in the frame once it has closed.

        Only apps this shell can observe closing (via on_app_close — see
        the sugar-next-next design doc's note on PID-watch limitations)
        are removed; apps launched outside the shell stay listed until
        universal window tracking exists.
        """
        if app_id not in self._running_ids:
            return
        self._running_ids.discard(app_id)
        child = self._running_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            if getattr(child, "app_id", None) == app_id:
                self._running_box.remove(child)
            child = next_child
