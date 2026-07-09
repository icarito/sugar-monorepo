# Sugar Next — Extension API

Sugar Next extensions are plain Python files. No GObject knowledge, no
registration step, no decorators, no packaging. The floor is deliberately
low: a working extension is ~5 lines.

## Writing an extension

Create a `.py` file in `~/.local/share/sugar-next/extensions/`
(or `$XDG_DATA_HOME/sugar-next/extensions/` if you set `XDG_DATA_HOME`):

```python
# ~/.local/share/sugar-next/extensions/hello.py

def on_shell_start():
    print("shell is up")

def on_app_launch(app_id, app_info):
    print(f"launching {app_id}")
```

That's it. The shell scans the directory at startup; any module-level
function whose name matches a known hook gets called when that hook fires.

## Available hooks

| Hook | Signature | Fires |
|------|-----------|-------|
| `on_shell_start` | `()` | Once, when the shell window is created |
| `on_app_launch` | `(app_id: str, app_info: Gio.AppInfo)` | Before an app launches from the grid |

`app_id` is the desktop-file id (e.g. `firefox.desktop`). `app_info` is a
`Gio.AppInfo` — you can call plain methods like `.get_display_name()` on it
without importing anything, but `from gi.repository import Gio` is available
if you want the full API.

More hooks (`on_app_close`, Journal integration) will be added based on
real usage — see the sugar-next OpenSpec change.

## Semantics and guarantees

- **Synchronous** — hooks run in the shell's main thread, before the
  triggering action proceeds. Keep them fast; long work should be spawned.
- **Best-effort isolation** — an exception in one extension is logged
  (logger `sugar-next.hooks`) and never breaks the shell or other
  extensions. A file that fails to import is skipped entirely.
- **Load order** — extension files load in sorted filename order; hooks
  are called in that order.
- **No reload** — extensions are scanned once at shell startup. Restart
  the shell to pick up changes.

## Examples

Two working examples live in `sugar-next/examples/extensions/`:

- `logger.py` — prints shell events to stdout.
- `launch-counter.py` — persists per-app launch counts to
  `~/.local/share/sugar-next/launch-counts.json`.

Install one by copying it into the extensions directory:

```sh
mkdir -p ~/.local/share/sugar-next/extensions
cp sugar-next/examples/extensions/logger.py ~/.local/share/sugar-next/extensions/
```

## Implementation

The scanner/dispatcher is `sugar_next/api/hooks.py` (`HookRegistry`). The
shell loads the registry in `SugarShell._on_activate`; `DesktopBundle.launch`
fires `on_app_launch`.
