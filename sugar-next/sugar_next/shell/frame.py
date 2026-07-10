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

    def __init__(self, bundle, palette_actions, on_palette_shown=None,
                 on_palette_closed=None):
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

        # Tell the Frame when this palette opens/closes so it won't hide
        # itself (on pointer-leave) while a palette is up — otherwise the
        # palette, which extends below the Frame, is unusable.
        if on_palette_shown is not None:
            self._palette.connect("show", lambda *_: on_palette_shown())
        if on_palette_closed is not None:
            self._palette.connect("closed", lambda *_: on_palette_closed())

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
        self.set_transition_duration(220)
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.FILL)

        provider = Gtk.CssProvider()
        provider.load_from_string(
            """
            .frame-bar {
                background-color: var(--sn-bg-alt);
                background: linear-gradient(180deg,
                    var(--sn-surface) 0%,
                    var(--sn-bg-alt) 3px,
                    var(--sn-bg-alt) 100%
                );
                border-bottom: 1px solid rgba(0, 0, 0, 0.12);
                border-radius: 0 0 14px 14px;
                padding: 8px 16px;
                min-height: 48px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
            }
            .frame-bar button {
                border-radius: 8px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                background: linear-gradient(180deg,
                    rgba(255,255,255,0.12) 0%,
                    rgba(0,0,0,0.04) 100%
                );
                box-shadow: 0 1px 0 rgba(255,255,255,0.15);
            }
            .frame-bar button:hover {
                background: linear-gradient(180deg,
                    var(--sn-accent) 0%,
                    rgba(0,0,0,0.08) 100%
                );
            }
            .frame-view-button {
                padding: 6px;
                min-width: 32px;
            }
            .frame-view-active {
                background: var(--sn-accent);
                color: white;
            }
            .frame-view-active image {
                -gtk-icon-filter: brightness(0) invert(1);
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

        # View switcher on the far left — [Desktop] [Apps] [Search].
        # Populated by set_view_switcher(); choosing a view is a
        # navigation concern owned by the Frame, not Settings.
        self._views_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4
        )
        self._views_box.add_css_class("frame-views")
        bar.append(self._views_box)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self._view_buttons = {}
        self._on_view_selected = None

        self._favorites_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4
        )
        bar.append(self._favorites_box)
        bar.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        self._running_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=4
        )
        bar.append(self._running_box)

        self._settings_button = Gtk.Button()
        self._settings_button.add_css_class("flat")
        self._settings_button.set_icon_name("emblem-system-symbolic")
        self._settings_button.set_has_frame(False)
        self._settings_button.set_hexpand(True)
        self._settings_button.set_halign(Gtk.Align.END)
        icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic")
        icon.set_pixel_size(20)
        self._settings_button.set_child(icon)
        bar.append(self._settings_button)

        self._open_palettes = 0
        self._favorite_ids = self._load_favorites()
        self._running_ids = set()
        self._rebuild_favorites()

    # -- palettes ----------------------------------------------------------

    def _on_palette_shown(self):
        self._open_palettes += 1

    def _on_palette_closed(self):
        self._open_palettes = max(0, self._open_palettes - 1)

    def has_open_palette(self):
        """True while any frame-item palette is open.

        The shell checks this before hiding the Frame on pointer-leave, so
        a palette (which extends below the Frame's edge) stays usable.
        """
        return self._open_palettes > 0

    def _make_item(self, bundle, palette_actions):
        return _FrameItem(
            bundle,
            palette_actions=palette_actions,
            on_palette_shown=self._on_palette_shown,
            on_palette_closed=self._on_palette_closed,
        )

    @property
    def settings_button(self):
        return self._settings_button

    def set_settings_panel(self, settings_window):
        self._settings_panel = settings_window
        self._settings_button.connect(
            "clicked", lambda _b: settings_window.popup()
        )

    # -- view switcher -----------------------------------------------------

    #: Symbolic icon per view. Falls back to a generic icon if a view id
    #: is unknown here, so extension-provided views still get a button.
    _VIEW_ICONS = {
        "desktop-grid": "user-home-symbolic",
        "app-grid": "view-app-grid-symbolic",
        "search-first": "system-search-symbolic",
    }
    _VIEW_ICON_FALLBACK = "view-grid-symbolic"

    def set_view_switcher(self, views, on_select, active_id=None):
        """Populate the view switcher.

        *views* is a list of ``(view_id, label)``. Buttons are symbolic
        icons (the label becomes the tooltip / accessible name).
        *on_select* is called with the chosen ``view_id`` when a button is
        clicked. The Frame closes after a selection.
        """
        self._on_view_selected = on_select
        while child := self._views_box.get_first_child():
            self._views_box.remove(child)
        self._view_buttons = {}
        for view_id, label in views:
            button = Gtk.Button()
            icon_name = self._VIEW_ICONS.get(view_id, self._VIEW_ICON_FALLBACK)
            image = Gtk.Image.new_from_icon_name(icon_name)
            image.set_pixel_size(20)
            button.set_child(image)
            button.set_tooltip_text(label)
            button.update_property(
                [Gtk.AccessibleProperty.LABEL], [label]
            )
            button.add_css_class("frame-view-button")
            button.connect("clicked", self._on_view_button_clicked, view_id)
            self._views_box.append(button)
            self._view_buttons[view_id] = button
        if active_id is not None:
            self.set_active_view(active_id)

    def _on_view_button_clicked(self, _button, view_id):
        self.set_active_view(view_id)
        if self._on_view_selected is not None:
            self._on_view_selected(view_id)
        self.set_reveal_child(False)

    def set_active_view(self, view_id):
        """Mark *view_id*'s button active (visual state only)."""
        for vid, button in self._view_buttons.items():
            if vid == view_id:
                button.add_css_class("frame-view-active")
            else:
                button.remove_css_class("frame-view-active")

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
            item = self._make_item(
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
        item = self._make_item(
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
