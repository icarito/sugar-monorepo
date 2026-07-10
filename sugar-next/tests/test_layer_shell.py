import types

from sugar_next.shell.layer_shell import (
    configure_shell_window,
    remove_layer_shell_preload_from_env,
)


class FakeLayerShell:
    class Layer:
        BACKGROUND = "background"
        BOTTOM = "bottom"

    class Edge:
        TOP = "top"
        BOTTOM = "bottom"
        LEFT = "left"
        RIGHT = "right"

    class KeyboardMode:
        ON_DEMAND = "on-demand"
        EXCLUSIVE = "exclusive"

    def __init__(self):
        self.calls = []

    def init_for_window(self, window):
        self.calls.append(("init_for_window", window))

    def set_layer(self, window, layer):
        self.calls.append(("set_layer", window, layer))

    def set_anchor(self, window, edge, anchored):
        self.calls.append(("set_anchor", window, edge, anchored))

    def set_namespace(self, window, namespace):
        self.calls.append(("set_namespace", window, namespace))

    def set_keyboard_mode(self, window, mode):
        self.calls.append(("set_keyboard_mode", window, mode))

    def set_exclusive_zone(self, window, zone):
        self.calls.append(("set_exclusive_zone", window, zone))


def test_configure_shell_window_returns_false_without_binding():
    assert configure_shell_window(object(), layer_shell=None) is False


def test_configure_shell_window_applies_layer_shell():
    window = object()
    layer_shell = FakeLayerShell()

    assert configure_shell_window(window, layer_shell=layer_shell) is True

    assert ("init_for_window", window) in layer_shell.calls
    assert ("set_layer", window, "background") in layer_shell.calls
    assert ("set_namespace", window, "sugar-next") in layer_shell.calls
    assert ("set_keyboard_mode", window, "on-demand") in layer_shell.calls
    assert ("set_exclusive_zone", window, -1) in layer_shell.calls
    anchors = [
        call[2]
        for call in layer_shell.calls
        if call[0] == "set_anchor" and call[3] is True
    ]
    assert set(anchors) == {"top", "bottom", "left", "right"}


def test_configure_shell_window_handles_incompatible_binding():
    broken = types.SimpleNamespace(init_for_window=lambda _window: 1 / 0)
    assert configure_shell_window(object(), layer_shell=broken) is False


def test_remove_layer_shell_preload_from_env_removes_only_helper():
    env = {
        "LD_PRELOAD": (
            "/usr/lib/libfirst.so:"
            "/usr/lib/liblayer-shell-preload.so:"
            "/opt/lib/liblast.so"
        )
    }

    remove_layer_shell_preload_from_env(env)

    assert env["LD_PRELOAD"] == "/usr/lib/libfirst.so:/opt/lib/liblast.so"


def test_remove_layer_shell_preload_from_env_unsets_when_only_helper():
    env = {"LD_PRELOAD": "/usr/lib/liblayer-shell-preload.so"}

    remove_layer_shell_preload_from_env(env)

    assert "LD_PRELOAD" not in env
