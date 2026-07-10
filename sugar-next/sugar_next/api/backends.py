"""Non-Python extension backends for Sugar Next.

The primary backend is Python (``importlib``, in-process — see hooks.py).
Extensions written in other languages run as **subprocesses** that speak a
line-delimited JSON protocol on stdin/stdout, which decouples the
extension language from the shell entirely.

Protocol (one JSON object per line):

    # shell -> extension (stdin)
    {"event": "on_app_launch", "args": {"app_id": "firefox.desktop", ...}}

    # extension -> shell (stdout)
    {"ok": true}
    {"cancel": true}          # veto (only meaningful for on_app_launch)
    {"error": "..."}          # logged; treated as no-op

Backends are best-effort, exactly like Python extensions: a subprocess
that crashes, hangs at startup, or emits an error is logged and skipped,
and can never take down the shell or other extensions.
"""

import json
import logging
import shutil
import subprocess

log = logging.getLogger("sugar-next.backends")

#: How long (seconds) to wait for a subprocess to answer a single event.
#: A hook that blocks longer is abandoned so one slow extension cannot
#: wedge the shell's synchronous hook dispatch.
_EVENT_TIMEOUT = 2.0


class SubprocessExtension:
    """Wrap a subprocess extension as a set of callable hook functions.

    Instead of importing a module, the loader asks this object for a
    callable per hook name via :meth:`hook`. Each call ships the event as
    one JSON line to the subprocess and reads one JSON line back.
    """

    #: Set so failures are attributed to a file, like Python extensions'
    #: ``fn.__module__`` in hooks.py logging.
    __module__ = "sugar_next_subprocess_ext"

    def __init__(self, name, argv):
        self._name = name
        self._argv = argv

    def hook(self, hook_name):
        """Return a callable delivering *hook_name* to the subprocess."""

        def _call(*args, **kwargs):
            return self._dispatch(hook_name, args, kwargs)

        return _call

    def _dispatch(self, hook_name, args, kwargs):
        # Only JSON-serialisable data crosses the boundary; drop the rest
        # (e.g. a Gio.AppInfo) rather than failing. Positional args are
        # named a0, a1, ... so the protocol stays a flat object.
        payload = {}
        for index, value in enumerate(args):
            if _json_safe(value):
                payload[f"a{index}"] = value
        for key, value in kwargs.items():
            if _json_safe(value):
                payload[key] = value

        message = json.dumps({"event": hook_name, "args": payload})
        try:
            proc = subprocess.Popen(
                self._argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (OSError, ValueError):
            log.exception("Failed to spawn extension %s", self._name)
            return None

        try:
            out, err = proc.communicate(message + "\n", timeout=_EVENT_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            log.warning("Extension %s timed out on %s", self._name, hook_name)
            return None

        if err:
            log.info("Extension %s stderr: %s", self._name, err.strip())

        response = _first_json_line(out)
        if response is None:
            return None
        if "error" in response:
            log.info("Extension %s error: %s", self._name, response["error"])
            return None
        # Surface a veto to the hook registry's launch-cancel contract.
        if response.get("cancel"):
            return {"cancel": True}
        return None


def _json_safe(value):
    return isinstance(value, (str, int, float, bool, type(None), list, dict))


def _first_json_line(text):
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except ValueError:
            continue
    return None


def _gjs_available():
    return shutil.which("gjs") is not None


def make_backend(path):
    """Return a :class:`SubprocessExtension` for *path*, or None.

    Dispatches on file type:
      - ``*.js``           -> gjs subprocess (if gjs is installed)
      - executable file    -> generic subprocess (runs the file directly)
    ``*.py`` is handled in-process by hooks.py and never reaches here.
    """
    if path.suffix == ".js":
        if not _gjs_available():
            log.info("Skipping %s: gjs not installed", path.name)
            return None
        return SubprocessExtension(path.name, ["gjs", str(path)])

    import os

    if os.access(path, os.X_OK):
        return SubprocessExtension(path.name, [str(path)])

    return None
