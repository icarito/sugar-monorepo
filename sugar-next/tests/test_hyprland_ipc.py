import json
import subprocess

from sugar_next.shell.hyprland_ipc import HyprlandIPC


class FakeRunner:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []

    def __call__(self, args, check):
        self.calls.append((args, check))
        key = tuple(args)
        return subprocess.CompletedProcess(args, 0, stdout=self.outputs.get(key, ""))


def test_snapshot_maps_clients_and_focus():
    runner = FakeRunner(
        {
            ("hyprctl", "clients", "-j"): json.dumps(
                [
                    {
                        "class": "org.gnome.Calculator",
                        "title": "Calculator",
                        "address": "0xabc",
                        "workspace": {"id": 1},
                        "mapped": True,
                    },
                    {"class": "", "title": "ignored"},
                    {"class": "hidden.App", "mapped": False},
                ]
            ),
            ("hyprctl", "activewindow", "-j"): json.dumps(
                {"class": "org.gnome.Calculator"}
            ),
            ("hyprctl", "workspaces", "-j"): json.dumps([{"id": 1, "name": "1"}]),
        }
    )

    state = HyprlandIPC(runner=runner).snapshot()

    assert [client.normalized_app_id for client in state.clients] == [
        "org.gnome.calculator"
    ]
    assert state.clients[0].title == "Calculator"
    assert state.clients[0].workspace_id == 1
    assert state.focused_app_id == "org.gnome.calculator"
    assert state.workspaces == ({"id": 1, "name": "1"},)


def test_focus_window_dispatches_by_normalized_class():
    runner = FakeRunner({})
    ipc = HyprlandIPC(runner=runner)

    assert ipc.focus_window("Org.Gnome.Calculator.desktop") is True
    assert runner.calls == [
        (
            [
                "hyprctl",
                "dispatch",
                'hl.dsp.focus({ window = "class:^org.gnome.calculator$" })',
            ],
            False,
        )
    ]
