"""Extension hook system for Sugar Next.

Extensions are plain Python files dropped into
``~/.local/share/sugar-next/extensions/``. Any module-level function whose
name matches a known hook is called when that hook fires. No registration
step, no decorators, no GObject knowledge required::

    # ~/.local/share/sugar-next/extensions/my-ext.py

    def on_shell_start():
        print("shell is up")

    def on_app_launch(app_id, app_info):
        print(f"launching {app_id}")

Hooks are synchronous and best-effort: an exception in one extension is
logged and never breaks the shell or other extensions.
"""

import importlib.util
import logging
import os
from pathlib import Path

log = logging.getLogger("sugar-next.hooks")

#: Hook names extensions may define. Signatures:
#:   on_shell_start()
#:   on_app_launch(app_id: str, app_info: Gio.AppInfo)
HOOK_NAMES = ("on_shell_start", "on_app_launch")


def extensions_dir() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return Path(data_home) / "sugar-next" / "extensions"


class HookRegistry:
    def __init__(self):
        self._hooks = {name: [] for name in HOOK_NAMES}
        self._loaded = False

    def load(self, directory=None):
        """Scan a directory for extension files and collect their hooks."""
        directory = Path(directory) if directory is not None else extensions_dir()
        self._hooks = {name: [] for name in HOOK_NAMES}
        self._loaded = True
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*.py")):
            module = self._import(path)
            if module is None:
                continue
            for name in HOOK_NAMES:
                fn = getattr(module, name, None)
                if callable(fn):
                    self._hooks[name].append(fn)
            log.info("Loaded extension %s", path.name)

    def _import(self, path):
        # Extension filenames may contain dashes, so they get a synthetic
        # module name instead of going through the import system.
        module_name = "sugar_next_ext_" + path.stem.replace("-", "_")
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception:
            log.exception("Failed to load extension %s", path)
            return None

    def call(self, hook_name, *args, **kwargs):
        """Invoke every extension implementing *hook_name*."""
        if not self._loaded:
            self.load()
        for fn in self._hooks.get(hook_name, ()):
            try:
                fn(*args, **kwargs)
            except Exception:
                log.exception(
                    "Extension hook %s failed in %s", hook_name, fn.__module__
                )


#: Shared registry used by the shell.
registry = HookRegistry()
