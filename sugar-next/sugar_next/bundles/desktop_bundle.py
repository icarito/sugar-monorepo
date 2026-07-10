import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib

from sugar_next.api.hooks import registry as hook_registry


def _watch_for_close(app_id, app_info, pid):
    """Fire on_app_close when *pid* exits.

    Only covers apps this shell itself launched (no
    wlr-foreign-toplevel-management support yet, so we can't observe
    windows we didn't spawn — see the sugar-next-next design doc).

    Note: Gio.AppInfo.launch() commonly reparents the launched process to
    the user's systemd instance (transient scope / portal activation)
    rather than forking it as our direct child, so the PID we watch is
    not our own child on those systems. GLib.child_watch_add() still
    fires reliably here because it falls back to polling /proc when
    waitpid() reports ECHILD — this works on Linux (Sugar Next's only
    target) but is not the "correct" parent-child watch mechanism. A
    fully correct implementation would track the systemd transient scope
    via org.freedesktop.systemd1 and watch its JobRemoved signal; that is
    unnecessary complexity for this v0.
    """

    def _on_exit(_pid, _status):
        hook_registry.call("on_app_close", app_id, app_info)
        GLib.spawn_close_pid(_pid)

    GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, _on_exit)


class DesktopBundle:
    def __init__(self, app_info):
        self.app_info = app_info

    @property
    def app_id(self):
        return self.app_info.get_id()

    @property
    def name(self):
        return self.app_info.get_display_name()

    @property
    def description(self):
        return self.app_info.get_description() or ""

    @property
    def icon(self):
        icon = self.app_info.get_icon()
        if icon:
            return icon
        return None

    @property
    def category(self):
        """First XDG category from the .desktop file, if any."""
        categories = self.app_info.get_categories()
        if not categories:
            return None
        return categories.split(";")[0] or None

    def launch(self):
        # An on_app_launch hook may veto the launch by returning
        # {"cancel": True}; extensions that return nothing let it proceed.
        if hook_registry.call_is_cancelled(
            "on_app_launch", self.app_id, self.app_info
        ):
            return False
        launch_context = Gio.AppLaunchContext()
        launch_context.connect("launched", self._on_launched)
        return self.app_info.launch(None, launch_context)

    def _on_launched(self, context, app_info, platform_data):
        pid = dict(platform_data).get("pid") if platform_data else None
        # DBusActivatable apps (Nautilus, GNOME Connections, ...) are
        # launched via a D-Bus Activate call rather than fork+exec, and
        # report pid=0 — not a real process to watch. GLib.child_watch_add
        # on pid 0 never fires, so the app would stay stuck in the Frame
        # forever. Skip close-tracking for these; on_app_close simply
        # never fires for them under the fallback path (real window
        # tracking via wlr-foreign-toplevel-management, when available,
        # is unaffected — it tracks windows, not processes).
        if pid:
            _watch_for_close(self.app_id, self.app_info, pid)

    @staticmethod
    def iter_apps():
        for app_info in Gio.AppInfo.get_all():
            try:
                if app_info.should_show():
                    yield DesktopBundle(app_info)
            except Exception:
                continue

    @staticmethod
    def sorted_apps():
        apps = list(DesktopBundle.iter_apps())
        apps.sort(key=lambda a: a.name.lower())
        return apps
