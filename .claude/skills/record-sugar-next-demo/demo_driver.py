#!/usr/bin/env python3
"""Scripted, no-input demo driver for Sugar Next.

Runs SugarShell with a canned sequence of view switches, favorite
pin/unpin, and Frame/Settings reveals, driven entirely by GLib timeouts
(no xdotool / real input needed — this works headless over any X11/
XWayland display). While it runs, an overlay caption box (bottom-center,
matching the style used in the original hand-made demo.mp4) shows a short
explanatory line for each beat.

Usage:
    python3 demo_driver.py &
    SHELL_PID=$!
    ffmpeg -f x11grab -window_id <id-from-record.sh> ... demo.mp4
    # driver exits on its own after the last beat; then stop ffmpeg

Normally invoked via record.sh, which also handles finding the window id
and driving ffmpeg. Run directly only for iterating on the beat sequence.
"""
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, GLib, Gtk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                 "sugar-next"))

from sugar_next.shell.main import SugarShell  # noqa: E402


class _Caption(Gtk.Label):
    """Bottom-center toast, styled like the original demo.mp4 captions."""

    _CSS = """
        .demo-caption {
            background: rgba(0, 0, 0, 0.75);
            color: white;
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 14pt;
        }
    """

    def __init__(self):
        super().__init__()
        self.add_css_class("demo-caption")
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.END)
        self.set_margin_bottom(28)
        self.set_visible(False)

        provider = Gtk.CssProvider()
        provider.load_from_string(self._CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def show_text(self, text):
        self.set_label(text)
        self.set_visible(True)

    def hide(self):
        self.set_visible(False)


class DemoDriver:
    """Runs *beats* (label, delay_ms, action) against a live SugarShell."""

    def __init__(self, app):
        self.app = app
        self.caption = _Caption()
        self._beats = []
        self._index = 0

    def attach_caption(self):
        # The shell builds its widget tree in _on_activate; the caption
        # is layered on top of everything via the outermost overlay.
        overlay = self.app.window.get_child()
        overlay.add_overlay(self.caption)

    def add(self, text, delay_ms, action=None):
        self._beats.append((text, delay_ms, action))
        return self

    def start(self, on_done=None):
        self._on_done = on_done
        self._run_next()

    def _run_next(self):
        if self._index >= len(self._beats):
            self.caption.hide()
            if self._on_done is not None:
                self._on_done()
            return
        text, delay_ms, action = self._beats[self._index]
        self._index += 1
        if action is not None:
            action()
        if text is not None:
            self.caption.show_text(text)
        GLib.timeout_add(delay_ms, self._advance)

    def _advance(self):
        self._run_next()
        return False


def build_default_script(app, driver):
    """The canned tour: Desktop (pie menu) -> Apps -> pin -> Desktop ->
    Frame -> Settings -> unpin -> back to empty Desktop."""

    def pick_first_app():
        from sugar_next.bundles.desktop_bundle import DesktopBundle
        apps = DesktopBundle.sorted_apps()
        return apps[0] if apps else None

    state = {}

    def to_apps():
        app._activate_view("app-grid")

    def to_desktop():
        app._activate_view("desktop-grid")

    def pin_one():
        bundle = pick_first_app()
        if bundle is not None:
            state["bundle"] = bundle
            app.pie_menu.pin_favorite(bundle)

    def open_frame():
        app.frame.reveal()

    def close_frame():
        app.frame.set_reveal_child(False)

    def open_settings():
        app._on_settings_requested()

    def close_settings():
        app.settings_panel.popdown()

    def unpin_one():
        bundle = state.get("bundle")
        if bundle is not None:
            app.pie_menu._unpin(bundle)

    # A no-op beat first: gives the window time to settle its layout
    # (the pie menu's centering depends on a real size allocation) before
    # the caption/recording script assumes it's ready.
    driver.add(None, 900)
    driver.add("Sugar Next — Desktop view: your pinned favorites, nothing else", 2200, to_desktop)
    driver.add("Empty on first run — pin apps from the Apps view to see them here", 2400)
    driver.add("F2 — Apps view: every installed app, search filters instantly", 2400, to_apps)
    driver.add("Pinning an app sends it to the Desktop pie menu", 2200, pin_one)
    driver.add("F1 — back to Desktop: the favorite is now a petal around Settings", 2600, to_desktop)
    driver.add("F6 (or the hot corner) opens the Frame — view switcher + running apps", 2600, open_frame)
    driver.add(None, 900, close_frame)
    driver.add("The pie menu's center button opens Settings — no separate button needed", 2600, open_settings)
    driver.add(None, 900, close_settings)
    driver.add("Right-click a petal to unpin", 2400, unpin_one)
    driver.add("pip install sugar-next — any Linux distro, GTK4, no legacy Sugar deps", 3200, to_desktop)


def main():
    app = SugarShell()
    driver = DemoDriver(app)

    def on_shell_ready(*_a):
        driver.attach_caption()
        build_default_script(app, driver)
        driver.start(on_done=lambda: GLib.timeout_add(500, lambda: (app.quit(), False)[1]))

    # _on_activate builds the window synchronously, so it's ready right
    # after 'activate' fires — hook the same signal, after SugarShell's
    # own handler (connect order = call order for the same signal).
    app.connect("activate", on_shell_ready)
    app.run([])


if __name__ == "__main__":
    main()
