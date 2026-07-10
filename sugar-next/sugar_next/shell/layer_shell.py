"""Optional GTK layer-shell integration for the Sugar Next shell window."""

from __future__ import annotations

import logging
import os

import gi

log = logging.getLogger("sugar-next.layer-shell")


_NAMESPACE_CANDIDATES = ("Gtk4LayerShell", "GtkLayerShell")
_LAYER_SHELL_PRELOAD_BASENAME = "liblayer-shell-preload.so"


def load_layer_shell():
    """Return a GI layer-shell module if one is available, else ``None``."""
    for namespace in _NAMESPACE_CANDIDATES:
        try:
            gi.require_version(namespace, "1.0")
            repository = __import__("gi.repository", fromlist=[namespace])
            return getattr(repository, namespace)
        except (ImportError, ValueError, AttributeError):
            continue
    return None


def configure_shell_window(window, layer_shell=None) -> bool:
    """Configure *window* as a layer-shell surface when bindings exist.

    Returns ``True`` when layer-shell was applied. Missing bindings or an
    incompatible module are non-fatal; the caller can keep its xdg_toplevel
    fallback and Hyprland window rules.
    """
    layer_shell = layer_shell or load_layer_shell()
    if layer_shell is None:
        return False

    try:
        layer_shell.init_for_window(window)
        _set_layer(layer_shell, window)
        _anchor_all_edges(layer_shell, window)
        _set_namespace(layer_shell, window, "sugar-next")
        _set_keyboard_mode(layer_shell, window)
        _set_exclusive_zone(layer_shell, window)
    except Exception:
        log.exception("failed to configure GTK layer-shell; using window fallback")
        return False

    return True


def remove_layer_shell_preload_from_env(env=None):
    """Remove gtk4-layer-shell's preload helper from an environment.

    The preload is needed for Sugar Next itself under PyGObject, but child
    apps must not inherit it or they may become layer-shell surfaces too.
    """
    env = env if env is not None else os.environ
    current = env.get("LD_PRELOAD")
    if not current:
        return

    kept = [
        entry
        for entry in current.split(":")
        if entry and os.path.basename(entry) != _LAYER_SHELL_PRELOAD_BASENAME
    ]
    if kept:
        env["LD_PRELOAD"] = ":".join(kept)
    else:
        env.pop("LD_PRELOAD", None)


def _set_layer(layer_shell, window):
    layer = _enum_value(layer_shell, "Layer", "BACKGROUND")
    if layer is None:
        layer = _enum_value(layer_shell, "Layer", "BOTTOM")
    if layer is not None and hasattr(layer_shell, "set_layer"):
        layer_shell.set_layer(window, layer)


def _anchor_all_edges(layer_shell, window):
    if not hasattr(layer_shell, "set_anchor"):
        return
    edge_names = ("TOP", "BOTTOM", "LEFT", "RIGHT")
    for edge_name in edge_names:
        edge = _enum_value(layer_shell, "Edge", edge_name)
        if edge is not None:
            layer_shell.set_anchor(window, edge, True)


def _set_namespace(layer_shell, window, namespace):
    if hasattr(layer_shell, "set_namespace"):
        layer_shell.set_namespace(window, namespace)


def _set_keyboard_mode(layer_shell, window):
    if not hasattr(layer_shell, "set_keyboard_mode"):
        return
    mode = _enum_value(layer_shell, "KeyboardMode", "ON_DEMAND")
    if mode is None:
        mode = _enum_value(layer_shell, "KeyboardMode", "EXCLUSIVE")
    if mode is not None:
        layer_shell.set_keyboard_mode(window, mode)


def _set_exclusive_zone(layer_shell, window):
    if hasattr(layer_shell, "set_exclusive_zone"):
        layer_shell.set_exclusive_zone(window, -1)


def _enum_value(module, enum_name, member_name):
    enum = getattr(module, enum_name, None)
    if enum is None:
        return None
    return getattr(enum, member_name, None)
