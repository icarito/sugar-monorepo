"""Smoke tests for language backends (subprocess extensions)."""

import os
import shutil
import stat
import sys

import pytest

from sugar_next.api.hooks import HookRegistry


def _write_exec(directory, name, body):
    path = directory / name
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


# A generic subprocess extension written in Python but run as an
# executable (not imported), exercising the language-agnostic backend.
_SUBPROC_EXT = """#!{py}
import json, sys
msg = json.loads(sys.stdin.readline())
trace = {trace!r}
with open(trace, 'a') as f:
    f.write(msg['event'] + ':' + str(msg['args']) + '\\n')
if msg['event'] == 'on_app_launch' and msg['args'].get('a0') == 'blocked.desktop':
    print(json.dumps({{'cancel': True}}))
else:
    print(json.dumps({{'ok': True}}))
"""


def test_python_backend_still_loads(tmp_path):
    # Python extensions keep working alongside the new backends.
    (tmp_path / "py_ext.py").write_text(
        "CALLS = []\n"
        "def on_shell_start():\n"
        "    open(%r, 'a').write('py\\n')\n" % str(tmp_path / "py.trace")
    )
    reg = HookRegistry()
    reg.load(tmp_path)
    reg.call("on_shell_start")
    assert (tmp_path / "py.trace").read_text().splitlines() == ["py"]


def test_generic_subprocess_backend(tmp_path):
    trace = tmp_path / "sub.trace"
    _write_exec(
        tmp_path,
        "sub-ext",  # no .py suffix -> generic executable backend
        _SUBPROC_EXT.format(py=sys.executable, trace=str(trace)),
    )
    reg = HookRegistry()
    reg.load(tmp_path)
    reg.call("on_shell_start")
    reg.call("on_app_launch", "foo.desktop", None)
    lines = trace.read_text().splitlines()
    assert "on_shell_start:{}" in lines
    # a0 is the app_id; a1 is the app_info (None here, still JSON-safe).
    assert any("'a0': 'foo.desktop'" in line for line in lines)


def test_subprocess_backend_can_cancel_launch(tmp_path):
    _write_exec(
        tmp_path,
        "veto-ext",
        _SUBPROC_EXT.format(py=sys.executable, trace=str(tmp_path / "v.trace")),
    )
    reg = HookRegistry()
    reg.load(tmp_path)
    assert reg.call_is_cancelled("on_app_launch", "blocked.desktop", None) is True
    assert reg.call_is_cancelled("on_app_launch", "allowed.desktop", None) is False


def test_broken_subprocess_is_isolated(tmp_path):
    # An executable that exits non-zero / prints garbage must not break
    # the shell or other extensions.
    _write_exec(tmp_path, "broken-ext", "#!/bin/sh\necho not-json\nexit 1\n")
    (tmp_path / "ok.py").write_text(
        "def on_shell_start():\n    open(%r,'a').write('ok\\n')\n"
        % str(tmp_path / "ok.trace")
    )
    reg = HookRegistry()
    reg.load(tmp_path)
    reg.call("on_shell_start")  # must not raise
    assert (tmp_path / "ok.trace").read_text().splitlines() == ["ok"]


def test_non_executable_non_py_is_ignored(tmp_path):
    (tmp_path / "notes.txt").write_text("just a data file\n")
    reg = HookRegistry()
    reg.load(tmp_path)
    reg.call("on_shell_start")  # must not raise


@pytest.mark.skipif(shutil.which("gjs") is None, reason="gjs not installed")
def test_gjs_backend(tmp_path):
    example = os.path.join(
        os.path.dirname(__file__), "..", "examples", "extensions", "logger.js"
    )
    shutil.copy(example, tmp_path / "logger.js")
    reg = HookRegistry()
    reg.load(tmp_path)
    # Just needs to run without raising; logger.js acks with {"ok": true}.
    reg.call("on_shell_start")
    assert reg.call_is_cancelled("on_app_launch", "foo.desktop", None) is False
