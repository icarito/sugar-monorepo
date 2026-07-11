"""Hosted-mode window-observation adapter: GNOME Shell extension over D-Bus.

Mutter does not implement wlr-foreign-toplevel-management (see
toplevel_tracker.py's docstring), so a normal Wayland client cannot
enumerate windows it did not launch while running inside GNOME. The
`sugar-next-windows` GNOME Shell extension (extensions/gnome-shell/)
watches Mutter's window list from inside GNOME Shell itself and
republishes open/close/focus events on the session bus; this module is
the client side, feeding the same app_state contract the standalone
adapter (toplevel_tracker.TopLevelTracker) feeds.
"""

from __future__ import annotations

import logging

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

log = logging.getLogger("sugar-next.gnome-window-source")

BUS_NAME = "org.sugarlabs.SugarNext.WindowSource"
OBJECT_PATH = "/org/sugarlabs/SugarNext/WindowSource"
INTERFACE_NAME = "org.sugarlabs.SugarNext.WindowSource"


class GnomeWindowSource:
    """Hosted-mode adapter: proxies the sugar-next-windows extension.

    Callbacks (*on_open*, *on_close*, *on_focus*) are invoked on the GTK
    main thread — Gio.DBusProxy signal delivery already happens on the
    thread-default main context, so no marshalling is needed here (unlike
    TopLevelTracker, which runs its own background thread).
    """

    def __init__(self, on_open=None, on_close=None, on_focus=None):
        self._on_open = on_open
        self._on_close = on_close
        self._on_focus = on_focus
        self._proxy = None
        self._available = None
        self._signal_id = None

    @property
    def available(self) -> bool:
        """Whether the extension's D-Bus name was reachable at start().

        None before start() has run, True/False after.
        """
        return self._available

    def start(self):
        try:
            self._proxy = Gio.DBusProxy.new_for_bus_sync(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.NONE,
                None,
                BUS_NAME,
                OBJECT_PATH,
                INTERFACE_NAME,
                None,
            )
        except GLib.Error:
            log.exception("Could not create proxy for %s", BUS_NAME)
            self._available = False
            return

        # DBusProxy.new_for_bus_sync succeeds even if nothing owns the
        # name yet (activatable-name semantics); g-name-owner is empty in
        # that case, which is how we detect "extension not installed or
        # not enabled" — this is the case the shell-startup spec requires
        # failing loudly on, not silently degrading.
        if not self._proxy.get_name_owner():
            log.warning(
                "%s has no owner; is the sugar-next-windows GNOME Shell "
                "extension installed and enabled?",
                BUS_NAME,
            )
            self._available = False
            return

        self._available = True
        self._signal_id = self._proxy.connect("g-signal", self._on_g_signal)

        # Enumerate windows already open before this adapter started.
        # D-Bus signals are only delivered for changes after subscription,
        # so existing windows would otherwise be invisible.
        try:
            result = self._proxy.call_sync(
                "ListWindows",
                None,
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            for app_id, title in result.unpack()[0]:
                if self._on_open is not None:
                    self._on_open(app_id, title)
        except GLib.Error:
            log.exception("ListWindows() failed")

        # Emit initial focus state.
        if self._on_focus is not None:
            try:
                result = self._proxy.call_sync(
                    "GetFocused",
                    None,
                    Gio.DBusCallFlags.NONE,
                    -1,
                    None,
                )
                app_id = result.unpack()[0]
                self._on_focus(app_id or None)
            except GLib.Error:
                log.exception("GetFocused() failed")

    def stop(self):
        if self._proxy is not None and self._signal_id is not None:
            self._proxy.disconnect(self._signal_id)
        self._signal_id = None
        self._proxy = None

    def focus_window(self, app_id: str) -> bool:
        if self._proxy is None:
            return False
        try:
            result = self._proxy.call_sync(
                "FocusWindow",
                GLib.Variant("(s)", (app_id,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error:
            log.exception("FocusWindow(%s) failed", app_id)
            return False
        return bool(result.unpack()[0])

    def _on_g_signal(self, _proxy, _sender, signal_name, parameters):
        args = parameters.unpack()
        if signal_name == "WindowOpened":
            app_id, title = args
            if self._on_open is not None:
                self._on_open(app_id, title)
        elif signal_name == "WindowClosed":
            (app_id,) = args
            if self._on_close is not None:
                self._on_close(app_id, "")
        elif signal_name == "WindowFocused":
            (app_id,) = args
            if self._on_focus is not None:
                self._on_focus(app_id or None)
