import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib

from sugar_next.api.hooks import registry as hook_registry


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

    def launch(self):
        hook_registry.call("on_app_launch", self.app_id, self.app_info)
        launch_context = Gio.AppLaunchContext()
        return self.app_info.launch(None, launch_context)

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
