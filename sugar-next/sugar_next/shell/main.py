#!/usr/bin/env python3
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, Gio

from sugar_next.api.hooks import registry as hook_registry
from sugar_next.shell.app_grid import SugarAppGrid
from sugar_next.shell.frame import SugarFrame


class SugarShell(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.sugarlabs.SugarNext")
        self.connect("activate", self._on_activate)

    def _on_activate(self, app):
        hook_registry.load()
        hook_registry.call("on_shell_start")
        self.window = Gtk.ApplicationWindow(
            application=app,
            title="Sugar Next",
            default_width=1024,
            default_height=768,
        )

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("window { background-color: #1a1a2e; }")
        Gtk.StyleContext.add_provider_for_display(
            self.window.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.frame = SugarFrame()
        self.app_grid = SugarAppGrid(
            on_launched=self.frame.add_running,
            on_pin=self.frame.pin_favorite,
        )

        overlay = Gtk.Overlay()
        overlay.set_child(self.app_grid)
        overlay.add_overlay(self.frame)
        self.window.set_child(overlay)

        # F6 toggles the Frame (Sugar's classic frame key).
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.window.add_controller(key_controller)

        # Top-right hot corner reveals the Frame.
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self._on_motion)
        self.window.add_controller(motion)

        self.window.present()

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_F6:
            self.frame.toggle()
            return True
        return False

    def _on_motion(self, controller, x, y):
        if y <= 2 and x >= self.window.get_width() - 2:
            self.frame.reveal()


def main():
    app = SugarShell()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()
