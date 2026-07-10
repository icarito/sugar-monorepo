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

    def on_peer_join(peer_id, peer_name):
        print(f"{peer_name} joined")

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
#:   on_app_close(app_id: str, app_info: Gio.AppInfo)
#:   on_peer_join(peer_id: str, peer_name: str)
#:   on_peer_leave(peer_id: str)
HOOK_NAMES = (
    "on_shell_start",
    "on_app_launch",
    "on_app_close",
    "on_peer_join",
    "on_peer_leave",
)


def extensions_dir() -> Path:
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
    )
    return Path(data_home) / "sugar-next" / "extensions"


#: Suffix appended to a disabled extension's filename. load() only globs
#: *.py, so a disabled extension (my-ext.py.disabled) is simply invisible
#: to the loader — no separate enabled/disabled list to keep in sync.
_DISABLED_SUFFIX = ".disabled"


def list_extensions(directory=None):
    """Return [(name, enabled)] for every extension file, enabled or not.

    *name* is the extension's base name (without .py or .py.disabled).
    """
    directory = Path(directory) if directory is not None else extensions_dir()
    if not directory.is_dir():
        return []
    entries = {}
    for path in directory.iterdir():
        if path.name.endswith(_DISABLED_SUFFIX) and path.name[: -len(_DISABLED_SUFFIX)].endswith(".py"):
            name = path.name[: -len(_DISABLED_SUFFIX)][: -len(".py")]
            entries[name] = False
        elif path.suffix == ".py":
            entries[path.stem] = True
    return sorted(entries.items())


def set_extension_enabled(name, enabled, directory=None):
    """Enable or disable the extension called *name* by renaming its file."""
    directory = Path(directory) if directory is not None else extensions_dir()
    enabled_path = directory / f"{name}.py"
    disabled_path = directory / f"{name}.py{_DISABLED_SUFFIX}"
    if enabled:
        if disabled_path.is_file():
            disabled_path.rename(enabled_path)
    else:
        if enabled_path.is_file():
            enabled_path.rename(disabled_path)


class HookRegistry:
    def __init__(self):
        self._hooks = {name: [] for name in HOOK_NAMES}
        self._internal_listeners = {name: [] for name in HOOK_NAMES}
        self._loaded = False

    def subscribe(self, hook_name, callback):
        """Register a shell-internal listener for *hook_name*.

        Unlike extension hooks (scanned from disk by load()), internal
        listeners are added directly by shell code — e.g. the Frame
        removing an app when on_app_close fires. Survives calls to
        load(), since load() only resets extension-provided hooks.
        """
        self._internal_listeners.setdefault(hook_name, []).append(callback)

    def load(self, directory=None):
        """Scan a directory for extension files and collect their hooks.

        Python extensions (``*.py``) run in-process. Other files are
        handed to a language backend (see ``api/backends.py``): ``*.js``
        via gjs, executables via a generic subprocess. Disabled
        extensions (``*.disabled``) are skipped by the globs below.
        """
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
        self._load_backends(directory)

    def _load_backends(self, directory):
        """Load non-Python extensions via subprocess language backends."""
        from sugar_next.api.backends import make_backend

        for path in sorted(directory.iterdir()):
            if path.suffix == ".py" or path.name.endswith(_DISABLED_SUFFIX):
                continue
            if not path.is_file():
                continue
            backend = make_backend(path)
            if backend is None:
                continue
            # A subprocess extension may implement any hook; the backend
            # dispatches by name, so register a caller for every hook.
            for name in HOOK_NAMES:
                self._hooks[name].append(backend.hook(name))
            log.info("Loaded extension %s (subprocess backend)", path.name)

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
        """Invoke every extension and internal listener for *hook_name*.

        Return values are collected and returned as a list, in call order
        (internal listeners first, then extensions). Callers that don't
        care about return values (most hooks) can ignore it.
        """
        if not self._loaded:
            self.load()
        results = []
        for fn in self._internal_listeners.get(hook_name, ()):
            try:
                results.append(fn(*args, **kwargs))
            except Exception:
                log.exception("Internal hook listener %s failed", hook_name)
        for fn in self._hooks.get(hook_name, ()):
            try:
                results.append(fn(*args, **kwargs))
            except Exception:
                log.exception(
                    "Extension hook %s failed in %s", hook_name, fn.__module__
                )
        return results

    def call_is_cancelled(self, hook_name, *args, **kwargs):
        """Call *hook_name* and report whether any hook cancelled.

        A hook cancels an action by returning a mapping with a truthy
        ``"cancel"`` key (e.g. ``{"cancel": True}``). Hooks that return
        nothing — the overwhelming majority — never cancel, so existing
        extensions keep working unchanged.
        """
        for result in self.call(hook_name, *args, **kwargs):
            if isinstance(result, dict) and result.get("cancel"):
                return True
        return False


#: Shared registry used by the shell.
registry = HookRegistry()
