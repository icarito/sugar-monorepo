## Extension Contract — Sugar Next

An **extension** is any file dropped into `~/.local/share/sugar-next/extensions/`
that implements one or more hook functions. The shell discovers, loads, and
calls them automatically. No registration, no config, no build step.

Extensions are **best-effort**: a broken extension is logged and skipped.
No extension can crash the shell or prevent other extensions from running.

This document defines the full contract. If you are reading this to write
your first extension, start with `examples/extensions/logger.py` (~8 lines).

---

### Hook functions

Hooks are plain module-level functions. Define any subset of those below.
Unknown functions are ignored.

| Hook | When called | Signature |
|------|-------------|-----------|
| `on_shell_start` | After the shell window is created, once per session | `on_shell_start()` |
| `on_app_launch` | Just before an application is launched | `on_app_launch(app_id: str, app_info: Gio.AppInfo)` |
| `on_app_close` | When the shell detects an application window has closed | `on_app_close(app_id: str)` |
| `on_peer_join` | When a peer is discovered on the local network | `on_peer_join(peer_id: str, peer_name: str)` |
| `on_peer_leave` | When a previously discovered peer disappears | `on_peer_leave(peer_id: str)` |

Signatures may grow optional keyword arguments in future versions.
Extensions MUST accept `**kwargs` if they want forward compatibility.

```python
def on_app_launch(app_id, app_info, **kwargs):
    print(f"launched {app_id}")
```

### Return values and launch-cancel

Hooks MAY return a value. Most hooks ignore it. The exception is
`on_app_launch`: returning a mapping with a truthy `"cancel"` key
(Python `{"cancel": True}`; subprocess `{"cancel": true}`) vetoes the
launch. Extensions that return nothing let the launch proceed, so
existing extensions keep working unchanged.

### Lifecycle

1. **Load**: `on_shell_start` scans `~/.local/share/sugar-next/extensions/*.py`
   and imports each file once.
2. **Call**: each hook fires synchronously when the event occurs. Hooks are
   called in filename order (sorted alphabetically).
3. **Reload**: the shell does not watch the extensions directory for changes.
   Restart the shell to pick up new or modified extensions.

### Enable / disable

Extensions are enabled by their `.py` extension and disabled by appending
`.disabled` to the filename. The Settings panel provides a UI for this.

| State | Filename |
|-------|----------|
| Enabled | `my-ext.py` |
| Disabled | `my-ext.py.disabled` |

### Language backends

The shell loads extensions written in **Python** in-process, and other
languages via a subprocess backend:

| Language | Mechanism | Status |
|----------|-----------|--------|
| Python | `importlib` — synchronous, in-process | Active |
| JavaScript (gjs) | `*.js` file run via `gjs <file>` as a subprocess, JSON on stdin/stdout | Active |
| Any language | Any **executable** file — run directly as a subprocess, JSON on stdin/stdout | Active |

The **subprocess protocol** (implemented in `sugar_next/api/backends.py`):

The shell spawns the extension once per event, writes one JSON object to
its stdin, and reads one JSON object from its stdout. Positional hook
arguments are passed as `a0`, `a1`, …; non-JSON arguments (e.g. a
`Gio.AppInfo`) are dropped. The subprocess must reply within a short
timeout or the event is abandoned.

```
# Shell → extension (stdin, one JSON object)
{"event": "on_app_launch", "args": {"a0": "firefox.desktop"}}

# Extension → shell (stdout, one JSON object)
{"ok": true}
# or, to veto an on_app_launch:
{"cancel": true}
# or, to report a fault (logged, treated as no-op):
{"error": "something went wrong"}
```

Routing: `*.js` → the gjs backend (skipped with a log line if `gjs` is
not installed); any other **executable** file → the generic subprocess
backend; `*.py` is always in-process. Same best-effort isolation as
Python: a crash, hang, or `{"error": ...}` is logged and never affects
the shell or other extensions.

### Error isolation

An exception in any single hook function is caught and logged. The shell
continues with the next hook function and the next extension. There is no
way for an extension to break the shell or other extensions.

### What extensions CANNOT do

- Block the shell from starting (hooks that hang will hang the shell;
  all hooks are synchronous).
- Persist across sessions without explicit storage (use XDG data dirs).
- Access the shell's internal state or windows (hooks receive only their
  documented arguments).

### Best practices

- Keep hooks fast. If you need I/O, do it in a thread.
- Use `kwargs` for forward compatibility.
- Log with `print()` — the shell captures stdout/stderr per extension.
- Store data in `~/.local/share/sugar-next/` (XDG_DATA_HOME).
- Store config in `~/.config/sugar-next/` (XDG_CONFIG_HOME).
