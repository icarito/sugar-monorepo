import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio

from sugar_next.bundles.desktop_bundle import DesktopBundle


def _marker_bundle(tmp_path):
    marker = tmp_path / "marker"
    desktop_file = tmp_path / "smoke.desktop"
    desktop_file.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Smoke\n"
        f"Exec=touch {marker}\n"
        "NoDisplay=true\n"
    )
    info = Gio.DesktopAppInfo.new_from_filename(str(desktop_file))
    return DesktopBundle(info), marker


def test_scanner_finds_apps():
    apps = DesktopBundle.sorted_apps()
    assert len(apps) > 0
    names = [a.name for a in apps]
    assert names == sorted(names, key=str.lower)


def test_bundle_properties(tmp_path):
    bundle, _ = _marker_bundle(tmp_path)
    assert bundle.name == "Smoke"
    assert bundle.app_id == "smoke.desktop"
    assert bundle.description == ""


def test_launch_runs_exec_and_fires_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    bundle, marker = _marker_bundle(tmp_path)

    fired = []
    from sugar_next.api import hooks

    monkeypatch.setattr(
        hooks.registry,
        "call",
        lambda name, *args, **kw: fired.append((name, args[0])),
    )

    assert bundle.launch() is True
    for _ in range(50):
        if marker.exists():
            break
        time.sleep(0.1)
    assert marker.exists()
    assert fired == [("on_app_launch", "smoke.desktop")]
