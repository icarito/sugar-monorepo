from sugar_next.api.hooks import HookRegistry


def _write(directory, name, body):
    path = directory / name
    path.write_text(body)
    return path


def _tracer(directory, filename, out_name):
    """Extension body that appends hook calls to a trace file."""
    trace = directory / out_name
    body = (
        f"TRACE = {str(trace)!r}\n"
        "def _log(what):\n"
        "    with open(TRACE, 'a') as f:\n"
        "        f.write(what + '\\n')\n"
        "def on_shell_start():\n"
        "    _log('start')\n"
        "def on_app_launch(app_id, app_info):\n"
        "    _log('launch:' + app_id)\n"
    )
    _write(directory, filename, body)
    return trace


def _trace_lines(trace):
    return trace.read_text().splitlines() if trace.exists() else []


def test_load_and_call(tmp_path):
    trace = _tracer(tmp_path, "good.py", "good.trace")
    registry = HookRegistry()
    registry.load(tmp_path)
    registry.call("on_shell_start")
    registry.call("on_app_launch", "foo.desktop", None)
    assert _trace_lines(trace) == ["start", "launch:foo.desktop"]


def test_broken_extension_is_isolated(tmp_path):
    _write(tmp_path, "broken.py", "raise RuntimeError('boom')\n")
    trace = _tracer(tmp_path, "works.py", "works.trace")
    registry = HookRegistry()
    registry.load(tmp_path)
    registry.call("on_shell_start")
    assert _trace_lines(trace) == ["start"]


def test_failing_hook_does_not_break_others(tmp_path):
    _write(
        tmp_path,
        "a_fails.py",
        "def on_shell_start():\n"
        "    raise ValueError('hook error')\n",
    )
    trace = _tracer(tmp_path, "b_works.py", "b.trace")
    registry = HookRegistry()
    registry.load(tmp_path)
    registry.call("on_shell_start")
    assert _trace_lines(trace) == ["start"]


def test_missing_directory_is_fine(tmp_path):
    registry = HookRegistry()
    registry.load(tmp_path / "does-not-exist")
    registry.call("on_shell_start")


def test_dashed_filenames(tmp_path):
    trace = _tracer(tmp_path, "my-ext.py", "my-ext.trace")
    registry = HookRegistry()
    registry.load(tmp_path)
    registry.call("on_shell_start")
    assert _trace_lines(trace) == ["start"]
