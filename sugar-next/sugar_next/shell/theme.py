"""Sugar Next color token system.

Defines the ``--sn-*`` CSS custom properties used throughout the shell,
computed from the system light/dark preference. Users may override any
token via ``~/.config/sugar-next/colors.css``, loaded after the base
stylesheet so overrides win through the normal CSS cascade.
"""

import os
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk

try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    _HAS_ADW = True
except (ImportError, ValueError):
    _HAS_ADW = False

#: Default accent used when no user override and no active-app tint apply.
DEFAULT_ACCENT = "#3584e4"

_LIGHT_TOKENS = {
    "--sn-bg": "#f6f6f6",
    "--sn-bg-alt": "#e8e8ea",
    "--sn-accent": DEFAULT_ACCENT,
    "--sn-text": "#1a1a1a",
    "--sn-text-secondary": "#5c5c5c",
    "--sn-surface": "#ffffff",
}

_DARK_TOKENS = {
    "--sn-bg": "#1a1a2e",
    "--sn-bg-alt": "#282850",
    "--sn-accent": DEFAULT_ACCENT,
    "--sn-text": "#f0f0f0",
    "--sn-text-secondary": "#b0b0b8",
    "--sn-surface": "#242438",
}

#: Token overrides applied on top of the base palette when contrast is
#: set to "high" — wider gap between text and background, no mid-gray.
_HIGH_CONTRAST_LIGHT = {
    "--sn-text": "#000000",
    "--sn-text-secondary": "#000000",
    "--sn-bg": "#ffffff",
    "--sn-surface": "#ffffff",
}

_HIGH_CONTRAST_DARK = {
    "--sn-text": "#ffffff",
    "--sn-text-secondary": "#ffffff",
    "--sn-bg": "#000000",
    "--sn-surface": "#000000",
}


def config_dir() -> Path:
    config_home = os.environ.get(
        "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
    )
    return Path(config_home) / "sugar-next"


def colors_override_file() -> Path:
    return config_dir() / "colors.css"


def prefers_dark() -> bool:
    if _HAS_ADW:
        style_manager = Adw.StyleManager.get_default()
        return style_manager.get_dark()
    settings = Gtk.Settings.get_default()
    if settings is not None:
        return bool(settings.get_property("gtk-application-prefer-dark-theme"))
    return True


def _tokens_css(tokens: dict) -> str:
    lines = ["window {"]
    for name, value in tokens.items():
        lines.append(f"    {name}: {value};")
    lines.append("}")
    return "\n".join(lines)


class ThemeManager:
    """Loads base + override CSS providers and lets the accent be updated."""

    def __init__(self):
        self._base_provider = Gtk.CssProvider()
        self._override_provider = Gtk.CssProvider()
        self._tint_provider = Gtk.CssProvider()
        self._contrast_provider = Gtk.CssProvider()
        self._tokens = dict(_DARK_TOKENS if prefers_dark() else _LIGHT_TOKENS)

    def apply(self, display=None):
        display = display or Gdk.Display.get_default()
        self._base_provider.load_from_string(_tokens_css(self._tokens))
        Gtk.StyleContext.add_provider_for_display(
            display, self._base_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        override_path = colors_override_file()
        if override_path.is_file():
            try:
                self._override_provider.load_from_path(str(override_path))
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    self._override_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1,
                )
            except Exception:
                pass

        Gtk.StyleContext.add_provider_for_display(
            display,
            self._tint_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 2,
        )
        Gtk.StyleContext.add_provider_for_display(
            display,
            self._contrast_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 3,
        )

    def set_contrast(self, level):
        """*level* is ``"normal"`` or ``"high"``."""
        if level != "high":
            self._contrast_provider.load_from_string("")
            return
        overrides = _HIGH_CONTRAST_DARK if prefers_dark() else _HIGH_CONTRAST_LIGHT
        self._contrast_provider.load_from_string(_tokens_css(overrides))

    def set_accent_tint(self, hex_color):
        """Dynamically override --sn-accent (e.g. from active-app palette)."""
        if hex_color is None:
            self._tint_provider.load_from_string("")
        else:
            self._tint_provider.load_from_string(
                f"* {{ --sn-accent: {hex_color}; }}"
            )

    def token(self, name):
        return self._tokens.get(name)


#: Shared theme manager used by the shell.
manager = ThemeManager()
