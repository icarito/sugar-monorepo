#!/usr/bin/env python3
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, GLib

from sugar_next.api.hooks import registry as hook_registry
from sugar_next.shell.app_grid import SugarAppGrid
from sugar_next.shell.search_first import SugarSearchFirst
from sugar_next.shell.desktop_grid import SugarDesktopGrid
from sugar_next.shell.frame import SugarFrame
from sugar_next.shell.home_view import HomeView
from sugar_next.shell.theme import manager as theme_manager
from sugar_next.shell.palette import dominant_color_hex
from sugar_next.shell.settings import SettingsPanel
from sugar_next.shell.settings_store import SettingsStore, icon_size_px
from sugar_next.shell.toplevel_tracker import TopLevelTracker


class SugarShell(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.sugarlabs.SugarNext")
        self.connect("activate", self._on_activate)
        self.connect("shutdown", self._on_shutdown)

    def _on_activate(self, app):
        hook_registry.load()
        hook_registry.call("on_shell_start")
        self.window = Gtk.ApplicationWindow(
            application=app,
            title="Sugar Next — A Learning Shell for Everyday Computing",
            default_width=1024,
            default_height=768,
        )

        self.settings_store = SettingsStore()
        theme_manager.apply(self.window.get_display())
        if self.settings_store.get("accent_color"):
            theme_manager.set_accent_tint(self.settings_store.get("accent_color"))
        theme_manager.set_contrast(self.settings_store.get("contrast"))

        base_css = Gtk.CssProvider()
        base_css.load_from_string(
            """
            window {
                background-color: var(--sn-bg);
                color: var(--sn-text);
            }
            button {
                border-radius: 10px;
                box-shadow: 0 1px 0 rgba(255,255,255,0.12);
            }
            button:hover {
                box-shadow: 0 1px 0 rgba(255,255,255,0.18),
                            0 2px 6px rgba(0,0,0,0.12);
            }
            searchbar, entry {
                border-radius: 12px;
                border: 1px solid rgba(0,0,0,0.1);
                background: linear-gradient(180deg,
                    rgba(0,0,0,0.03) 0%,
                    rgba(0,0,0,0.01) 100%
                );
                box-shadow:
                    inset 0 1px 2px rgba(0,0,0,0.06),
                    0 1px 0 rgba(255,255,255,0.08);
            }
            .sn-dropdown {
                border: none;
                box-shadow: none;
                background: none;
                margin: 0;
                padding: 0 4px;
                min-height: 28px;
            }
            .sn-dropdown > button {
                border-radius: 8px;
                border: 1px solid rgba(0,0,0,0.12);
                background: linear-gradient(180deg,
                    rgba(255,255,255,0.08) 0%,
                    rgba(0,0,0,0.02) 100%
                );
                box-shadow: 0 1px 0 rgba(255,255,255,0.08);
                padding: 2px 10px;
            }
            .sn-dropdown > button:hover {
                border-color: rgba(0,0,0,0.20);
            }
            .sn-dropdown > popover {
                border-radius: 10px;
                border: 1px solid rgba(0,0,0,0.12);
                box-shadow: 0 3px 12px rgba(0,0,0,0.18);
                padding: 4px 0;
            }
            .sn-dropdown > popover contents > row {
                padding: 4px 12px;
            }
            .sn-dropdown > popover contents > row:hover {
                background: var(--sn-accent);
                color: white;
            }
            .frame-handle {
                min-width: 52px;
                min-height: 14px;
                padding: 0;
                margin-top: 0;
                border: none;
                border-radius: 0 0 8px 8px;
                background: var(--sn-accent);
                opacity: 0.6;
                box-shadow: 0 1px 3px rgba(0,0,0,0.35);
                transition: opacity 150ms ease;
            }
            .frame-handle:hover {
                opacity: 0.95;
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            self.window.get_display(),
            base_css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.frame = SugarFrame()

        self.toplevel_tracker = TopLevelTracker(
            on_open=self._on_toplevel_open,
            on_close=self._on_toplevel_close,
        )
        self.toplevel_tracker.start()
        hook_registry.subscribe(
            "on_app_close", lambda app_id, app_info: self._on_app_process_closed(app_id)
        )

        icon_size = icon_size_px(self.settings_store.get("icon_size"))
        self.app_grid = SugarAppGrid(
            on_launched=self._on_app_launched,
            on_pin=self.frame.pin_favorite,
            icon_size=icon_size,
        )
        self.search_first = SugarSearchFirst(
            on_launched=self._on_app_launched, icon_size=icon_size
        )
        self.search_first.set_bundles(self.app_grid._load_bundles())

        bundled = self.app_grid._load_bundles()
        self.desktop_grid = SugarDesktopGrid(
            background_path=self.settings_store.get("background_path")
        )
        self.desktop_grid.set_on_launch(self._on_app_launched)
        self.desktop_grid.set_icon_size(icon_size)
        self.desktop_grid.populate(bundled)

        self.home_view = HomeView()
        self.home_view.add_view(self.app_grid)
        self.home_view.add_view(self.search_first)
        self.home_view.add_view(self.desktop_grid, set_active=True)

        # Views are navigated from the Frame (Desktop / Apps / Search),
        # not selected in Settings. Map the user-facing view onto the
        # underlying layout id. Order here is the Frame button order.
        self._views = [
            ("desktop-grid", "Desktop"),
            ("app-grid", "Apps"),
            ("search-first", "Search"),
        ]

        # Restore the last active view, or start in Desktop on first run.
        saved_layout = self.settings_store.get("home_view_layout")
        if saved_layout in self.home_view.view_ids():
            self.home_view.set_active(saved_layout)
        else:
            self.home_view.set_active("desktop-grid")

        self._background_picture = Gtk.Picture()
        self._background_picture.set_content_fit(Gtk.ContentFit.COVER)
        self._background_picture.set_can_shrink(True)
        bg_path = self.settings_store.get("background_path")
        if bg_path:
            self._background_picture.set_filename(bg_path)
        self._background_picture.add_css_class("home-view-bg")

        # Background adjustment overlay. A single flat wash drawn over the
        # wallpaper and *under* the Home View, so every layout (app-grid,
        # search-first, desktop-grid) sees the same treatment.
        #   brightness: -1.0 (black) .. 0 (none) .. +1.0 (white)
        #   contrast:    0.0 (none)  .. 1.0 (flat mid-grey veil)
        self._bg_brightness = float(self.settings_store.get("bg_brightness"))
        self._bg_contrast = float(self.settings_store.get("bg_contrast"))

        self._bg_overlay = Gtk.DrawingArea()
        self._bg_overlay.set_hexpand(True)
        self._bg_overlay.set_vexpand(True)
        self._bg_overlay.set_can_target(False)
        self._bg_overlay.add_css_class("home-view-bg-overlay")
        self._bg_overlay.set_draw_func(self._draw_bg_overlay)

        home_overlay = Gtk.Overlay()
        home_overlay.set_child(self._background_picture)
        home_overlay.add_overlay(self._bg_overlay)
        home_overlay.add_overlay(self.home_view)

        shell_overlay = Gtk.Overlay()
        shell_overlay.set_child(home_overlay)
        shell_overlay.add_overlay(self.frame)
        self.window.set_child(shell_overlay)
        shell_overlay._frame = self.frame

        # Visible pull-down handle at the top-center — a small accent pill
        # that reveals the Frame on click or hover. Centered so it never
        # overlaps the Frame's settings button at the right edge. It hides
        # itself while the Frame is open (the Frame's own top edge takes
        # over) and reappears when the Frame is dismissed.
        self._hot_corner = Gtk.Button()
        self._hot_corner.add_css_class("frame-handle")
        self._hot_corner.set_halign(Gtk.Align.CENTER)
        self._hot_corner.set_valign(Gtk.Align.START)
        self._hot_corner.set_tooltip_text("Click or hover to reveal the Frame")
        self._hot_corner.connect("clicked", self._on_handle_clicked)
        shell_overlay.add_overlay(self._hot_corner)

        # Keep the handle out of the way whenever the Frame is showing.
        self.frame.connect(
            "notify::child-revealed", self._on_frame_reveal_changed
        )

        # Classic-Sugar auto-Frame: reveal the Frame when the shell loses
        # focus (an activity has taken the screen, so the user always has a
        # way back). It is NOT hidden when the window regains focus — the
        # Frame lives inside the shell window, so regaining window focus is
        # not the same as leaving the Frame. Instead it hides when the
        # pointer leaves the Frame's own area (see the motion controller on
        # ``self.frame`` below). A manual dismiss is respected until the
        # next focus change.
        self._frame_manually_dismissed = False
        # Clicking the handle *pins* the Frame open: a deliberate act, so
        # it must not close just because the pointer moves into the window.
        # Only another click on the handle (toggle), F6, or a background
        # click dismisses a pinned Frame. Hovering the handle still reveals
        # a transient, unpinned Frame that hides on pointer-leave.
        self._frame_pinned = False
        # Monotonic time (µs) until which a spurious pointer `leave` right
        # after revealing the Frame must be ignored. Revealing slides the
        # Frame out from under the pointer, which fires `leave` immediately
        # and would otherwise snap it shut so a click "does nothing".
        self._frame_leave_guard_until = 0
        self.window.connect("notify::is-active", self._on_window_active_changed)

        # Hide the Frame once the pointer leaves it (but not while the shell
        # is unfocused — then an activity owns the screen and the Frame
        # should stay put as the way back).
        frame_motion = Gtk.EventControllerMotion()
        frame_motion.connect("leave", self._on_frame_pointer_left)
        self.frame.add_controller(frame_motion)

        # Click outside the Frame closes it.
        close_gesture = Gtk.GestureClick()
        close_gesture.connect("pressed", self._on_background_pressed)
        home_overlay.add_controller(close_gesture)

        self.settings_panel = SettingsPanel(
            home_view=self.home_view, store=self.settings_store, shell=self
        )
        self.frame.set_settings_panel(self.settings_panel)
        self.frame.set_view_switcher(
            self._views,
            self._on_view_selected,
            active_id=self.home_view.active_id,
        )

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.window.add_controller(key_controller)

        # Motion on the hot corner itself (keeping the old behavior).
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self._hot_corner.add_controller(motion)

        self.window.present()

    def _on_window_active_changed(self, window, _pspec):
        # Focus changed: this is a fresh context, so any earlier manual
        # dismiss no longer applies.
        self._frame_manually_dismissed = False
        if not window.get_property("is-active"):
            # Shell lost focus (an activity took over) — surface the Frame
            # as the user's way back. Regaining focus does *not* hide it;
            # that is left to the pointer leaving the Frame.
            self.frame.reveal()

    def _reveal_frame(self):
        # Guard against the `leave` that fires as the Frame slides out from
        # under the pointer, so it doesn't immediately close again.
        self._frame_leave_guard_until = GLib.get_monotonic_time() + 400_000
        self.frame.reveal()

    def _on_handle_clicked(self, _button):
        # Clicking toggles a pinned Frame: pin it open, or unpin+close if
        # it is already pinned.
        if self._frame_pinned and self.frame.get_reveal_child():
            self._frame_pinned = False
            self.frame.set_reveal_child(False)
        else:
            self._frame_pinned = True
            self._reveal_frame()

    def _on_frame_pointer_left(self, _controller):
        # A pinned Frame (opened by clicking the handle) stays put no
        # matter where the pointer goes; only an explicit dismiss closes it.
        if self._frame_pinned:
            return
        # Ignore the spurious leave right after a reveal (see _reveal_frame).
        if GLib.get_monotonic_time() < self._frame_leave_guard_until:
            return
        # Keep the Frame open while an item palette is up — the palette
        # extends below the Frame, so the pointer "leaves" the Frame to
        # use it; hiding now would make the palette unusable.
        if self.frame.has_open_palette():
            return
        # Pointer left the Frame. Tuck it away — unless the shell is
        # unfocused, in which case an activity owns the screen and the
        # Frame must remain as the way back.
        if self.window.get_property("is-active"):
            self.frame.set_reveal_child(False)

    def _on_background_pressed(self, gesture, n_press, x, y):
        # Explicit dismiss: unpin and remember it so auto-Frame does not
        # immediately re-open while the shell stays unfocused.
        self._frame_pinned = False
        if not self.window.get_property("is-active"):
            self._frame_manually_dismissed = True
        self.frame.set_reveal_child(False)

    #: Direct keybindings to views (frame-views spec): F1/F2/F3.
    _VIEW_KEYS = {
        Gdk.KEY_F1: "desktop-grid",
        Gdk.KEY_F2: "app-grid",
        Gdk.KEY_F3: "search-first",
    }

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_F6:
            # F6 is a deliberate act, like clicking the handle: it pins the
            # Frame open, or unpins+closes it if already open.
            if self.frame.get_reveal_child():
                self._frame_pinned = False
                if not self.window.get_property("is-active"):
                    self._frame_manually_dismissed = True
                self.frame.set_reveal_child(False)
            else:
                self._frame_pinned = True
                self._reveal_frame()
            return True
        if keyval in self._VIEW_KEYS:
            self._activate_view(self._VIEW_KEYS[keyval])
            return True
        if keyval == Gdk.KEY_F10:
            if self.settings_panel.is_visible():
                self.settings_panel.popdown()
            else:
                self.frame.reveal()
                self.settings_panel.popup()
            return True
        return False

    def _activate_view(self, view_id):
        """Switch to *view_id*, persist it, and sync the Frame switcher."""
        if view_id not in self.home_view.view_ids():
            return
        self.home_view.set_active(view_id)
        self.frame.set_active_view(view_id)
        self.settings_store.set("home_view_layout", view_id)

    def _on_view_selected(self, view_id):
        # Called when a Frame view button is clicked. The Frame closes
        # after selection (handled in frame.py), so drop any pin.
        self._frame_pinned = False
        self._activate_view(view_id)

    def _on_motion(self, controller, x, y):
        if y <= 3:
            self._reveal_frame()

    def _on_frame_reveal_changed(self, frame, _pspec):
        # Fade the pull-down handle out while the Frame is visible instead
        # of hiding it: set_visible(False) collapses the overlay child and
        # forces a re-layout mid-animation, which makes the Frame "jump".
        # Opacity + can_target keeps its slot reserved, so no reflow.
        revealed = frame.get_child_revealed()
        self._hot_corner.set_opacity(0.0 if revealed else 1.0)
        self._hot_corner.set_can_target(not revealed)

    def _on_shutdown(self, app):
        self.toplevel_tracker.stop()

    def _on_app_launched(self, bundle):
        self.frame.add_running(bundle)
        if self.settings_store.get("accent_color"):
            return
        color = dominant_color_hex(bundle.icon)
        theme_manager.set_accent_tint(color)

    def _draw_bg_overlay(self, area, cr, width, height):
        # Contrast: a flat mid-grey veil that mutes the wallpaper toward
        # grey so foreground labels/icons keep their footing.
        if self._bg_contrast > 0:
            cr.set_source_rgba(0.5, 0.5, 0.5, self._bg_contrast)
            cr.paint()
        # Brightness: push toward white (positive) or black (negative).
        b = self._bg_brightness
        if b > 0:
            cr.set_source_rgba(1, 1, 1, min(b, 1.0))
            cr.paint()
        elif b < 0:
            cr.set_source_rgba(0, 0, 0, min(-b, 1.0))
            cr.paint()

    def set_background(self, path):
        if path:
            self._background_picture.set_filename(path)
        else:
            self._background_picture.set_filename(None)

    def set_bg_brightness(self, value):
        self._bg_brightness = float(value)
        self._bg_overlay.queue_draw()

    def set_bg_contrast(self, value):
        self._bg_contrast = float(value)
        self._bg_overlay.queue_draw()

    def _on_toplevel_open(self, wayland_app_id, title):
        pass

    def _on_toplevel_close(self, wayland_app_id, title):
        if self.toplevel_tracker.available is not True:
            return
        if not self._has_open_toplevel(wayland_app_id):
            self.frame.remove_running(wayland_app_id)

    def _has_open_toplevel(self, wayland_app_id):
        return any(
            state.get("app_id") == wayland_app_id
            for state in self.toplevel_tracker._toplevels.values()
        )

    def _on_app_process_closed(self, app_id):
        if self.toplevel_tracker.available is True:
            return
        self.frame.remove_running(app_id)


def main():
    app = SugarShell()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
