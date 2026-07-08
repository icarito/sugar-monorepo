---
name: sugar-activity-dev
description: Use when the user wants to create, modify, or test a Sugar activity — understanding the Activity class API, bundle format, activity lifecycle, toolbar/canvas patterns, or setting up activity repos with git subtree/subrepo for development.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# Sugar Activity Development

Workflows for developing Sugar activities using `sugar-toolkit-gtk4` —
the Activity class API, bundle format, testing in nested compositors,
and project structure conventions.

## Activity class API

### Minimal activity (GTK4 / sugar-toolkit-gtk4)

```python
from sugar4.activity.activity import Activity

class MyActivity(Activity):
    def __init__(self, handle):
        super().__init__(handle)
        self._setup_ui()

    def _setup_ui(self):
        self._canvas = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_canvas(self._canvas)
        label = Gtk.Label(label="Hello Sugar")
        self._canvas.append(label)
        self.show_all()
```

Key methods inherited from `Activity`:

- `__init__(self, handle)` — receives an `ActivityHandle` from the shell.
  Call `super().__init__(handle)` before any UI setup.
- `set_canvas(widget)` — sets the activity's main content area. The
  canvas widget is packed between the toolbar and any secondary toolbar.
- `build_toolbar()` — override to return a `Gtk.Widget` that becomes the
  activity's toolbar. Default returns `None` (no toolbar).
- `get_toolbar()` — call to retrieve the toolbar widget set by
  `build_toolbar()`. Used by the shell.
- `show_all()` — shows the activity window. Call after UI setup.
- `get_title()` / `set_title(title)` — get/set the activity window title.
- `get_bundle_id()` — returns the activity's bundle ID string.
- `get_activity_root()` — path to the activity bundle directory on disk.
- `read_file(file_path)` — called when the activity is asked to load a
  file from the Journal. Override to handle loading.
- `write_file(file_path)` — called when the activity is asked to save to
  the Journal. Override to handle saving.
- `can_close()` — return `True` if the activity can be closed (no unsaved
  work). Override to implement save-before-close prompts.

### ActivityHandle API

The handle passed to `__init__` provides coordination with the shell:

```python
handle.get_id()           # unique activity instance ID
handle.get_bundle_id()    # bundle identifier string
handle.get_bundle_path()  # filesystem path to bundle
handle.get_activity_root()# working directory for the activity
handle.get_shared()       # True if this is a shared activity
handle.get_colors()       # Sugar user colors for activity branding
handle.get_title()        # initial title from Journal metadata
```

### Lifecycle hooks

```python
class MyActivity(Activity):
    def __init__(self, handle):
        super().__init__(handle)
        # PERSISTENT: set up state, load saved data

    def build_toolbar(self):
        # PERSISTENT: toolbar is built once and kept across starts
        return self._toolbar

    def start(self):
        # UI-RELEVANT: called when activity becomes visible
        # Rebuild canvas, reconnect signals
        # Sugar may call start() → stop() → start() without re-creating
        # the Activity object
        self._setup_ui()

    def stop(self):
        # UI-RELEVANT: called when activity becomes hidden (switching
        # activities, Frame overlay, etc.)
        # Disconnect signal handlers, destroy canvas children
        # Keep persistent state (loaded data, toolbar)
        pass

    def destroy(self):
        # FINAL: activity is being terminated
        # Clean up everything, release resources
        pass
```

The start/stop cycle is Sugar-specific: when a user switches activities,
the old one is "stopped" (hidden, signals disconnected) but not destroyed,
and the new one is "started". This is for fast switching — the Activity
object itself survives the full session but its canvas content doesn't.

## Bundle format and validation

### Directory structure

```
MyActivity.activity/
  activity.info         # bundle metadata (required)
  activity.svg           # icon (optional)
  __init__.py            # entry point: must export a callable
  mymodule.py            # activity code
  resources/             # images, sounds, etc.
```

### activity.info format

A dot-file-format key=value file:

```ini
[Activity]
name = My Activity
bundle_id = org.sugarlabs.MyActivity
activity_version = 1
release = 1
license = MIT
exec = sugar-activity3
icon = activity-myactivity
mime_types = text/plain;image/png
summary = A short description of the activity
repository = https://github.com/username/my-activity
```

Key fields:
- `name` — human-readable name shown in the Home View activity ring.
- `bundle_id` — unique identifier, often reverse-DNS.
- `exec` — command to launch. `sugar-activity3` is the standard loader
  for GTK3 toolkit; GTK4 toolkit activities use `sugar-activity4`.
- `icon` — icon name (without extension, Sugar appends `-72.svg` or
  `-100.svg` by convention).
- `mime_types` — semicolon-separated list of MIME types this activity
  can open.
- `repository` — source repo URL (informational, not used at runtime).

### Validating a bundle

Sugar checks `activity.info` at activity install time:

```bash
# Manual validation: check the file is parseable
python3 -c "
import configparser
c = configparser.ConfigParser()
c.read('MyActivity.activity/activity.info')
print(c['Activity']['bundle_id'])
"
```

The shell validates at runtime:
- `activity.info` must exist and be readable.
- `bundle_id` must be present and non-empty.
- `exec` must name an installed command or a path inside the bundle.

### Installing for testing

Sugar looks for activities in `~/Activities/`. For development:

```bash
# Symlink (recommended for active dev — no reinstall after edits)
ln -s "$(pwd)/MyActivity.activity" ~/Activities/

# Copy (for testing the install flow itself)
cp -r MyActivity.activity ~/Activities/
```

Sugar auto-discovers bundles in `~/Activities/` at startup — no
separate "install" step needed.

## Using git subtree/subrepo for activities

Activities are standalone repos, not submodules of the Sugar workspace.
For co-development (modifying both toolkit and an activity):

### Option 1: git subtree (recommended for active co-dev)

Add the activity repo as a subtree in the workspace:

```bash
# From workspace root:
git subtree add --prefix=repos/my-activity \
  https://github.com/sugarlabs/my-activity.git main --squash

# Pull updates from upstream:
git subtree pull --prefix=repos/my-activity \
  https://github.com/sugarlabs/my-activity.git main --squash

# Push changes back:
git subtree push --prefix=repos/my-activity \
  https://github.com/sugarlabs/my-activity.git main
```

Then symlink into `~/Activities/` for Sugar to find:

```bash
ln -s "$(pwd)/repos/my-activity" ~/Activities/MyActivity.activity
```

### Option 2: standalone clone

```bash
git clone https://github.com/sugarlabs/my-activity ~/Activities/MyActivity.activity
```

Simpler, but separates history from the workspace — harder to coordinate
toolkit changes with activity changes in a single PR.

### Option 3: pip install -e (for toolkit-only activities)

If the activity repo has a `setup.py` or `pyproject.toml`:

```bash
source repos/sugar-toolkit-gtk4/.venv/bin/activate
pip install -e repos/my-activity
```

This makes the activity importable without symlinking.

## Testing activities in nested Wayfire

Activities run as Wayland clients inside jarabe's compositor, or
standalone in a nested Wayfire window. For standalone testing:

```bash
# Start nested Wayfire
wayfire &
# Wait for "Using socket name wayland-1"

# Run the activity pointed at that session
WAYLAND_DISPLAY=wayland-1 \
  GI_TYPELIB_PATH="$HOME/.local/lib/girepository-1.0:$GI_TYPELIB_PATH" \
  SUGAR_BUNDLE_PATH="$HOME/Activities/MyActivity.activity" \
  SUGAR_BUNDLE_NAME="My Activity" \
  SUGAR_BUNDLE_ID="org.sugarlabs.MyActivity" \
  python3 -m myactivity
```

For `SimpleActivity`-based examples (from `sugar-toolkit-gtk4/examples/`):

```bash
WAYLAND_DISPLAY=wayland-1 \
  SUGAR_BUNDLE_PATH=examples/activity \
  SUGAR_BUNDLE_NAME=Test \
  SUGAR_BUNDLE_ID=org.sugarlabs.Test \
  ../sugar-toolkit-gtk4/.venv/bin/python3 examples/basic_activity.py
```

The `SimpleActivity` subclass handles its own `Gtk.Application` loop,
unlike full `Activity` subclasses which expect jarabe to provide the
application context.

## Activity toolbar and canvas patterns

### Standard toolbar structure

```python
from sugar4.graphics.toolbar import ActivityToolbar, StopButton

class MyActivity(Activity):
    def build_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        # Activity toolbar (left): title entry + share button + description
        self._activity_toolbar = ActivityToolbar(self)
        toolbar.append(self._activity_toolbar)

        # Spacer: pushes the stop button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)

        # Stop button (right): close the activity
        stop = StopButton(self)
        toolbar.append(stop)

        toolbar.add_css_class("toolbar")
        return toolbar
```

### Pattern: toolbar actions that modify canvas

```python
class DrawActivity(Activity):
    def build_toolbar(self):
        toolbar = ActivityToolbar(self)

        color_button = Gtk.ColorDialogButton()
        color_button.connect("notify::rgba", self._on_color_changed)
        toolbar.append(color_button)

        clear_button = Gtk.Button(label="Clear")
        clear_button.connect("clicked", self._on_clear)
        toolbar.append(clear_button)

        return toolbar

    def _on_color_changed(self, button, pspec):
        self._current_color = button.get_rgba()

    def _on_clear(self, button):
        # Remove old canvas content
        child = self._canvas.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self._canvas.remove(child)
            child = next_child
        # Rebuild
        self._setup_drawing_area()
```

### Pattern: Journal save/restore

```python
class NotesActivity(Activity):
    def write_file(self, file_path):
        with open(file_path, "w") as f:
            f.write(self._text_buffer.get_text())

    def read_file(self, file_path):
        with open(file_path, "r") as f:
            self._text_buffer.set_text(f.read())

    def _on_text_changed(self, buffer):
        # Sugar auto-saves when metadata changes
        self.metadata["text_changed"] = "1"
```

Journal metadata (`self.metadata`) is a dict-like object synced to the
datastore. Setting keys triggers auto-save. Common metadata keys:
- `title` — document title (shown in Journal)
- `description` — short description
- `mime_type` — MIME type of saved file
- `preview` — path to a PNG preview image
- `icon-color` — Sugar user color associated with the entry

## Notes

- `Activity` vs `SimpleActivity`: `Activity` expects jarabe to provide
  the `Gtk.Application` context and manages its own window lifecycle.
  `SimpleActivity` extends `Gtk.Application` and manages its own
  application loop — use it for standalone examples and tests.
- The toolbar is persistent across start/stop cycles. Don't put
  canvas-specific controls in the toolbar — rebuild canvas controls
  inside `start()`.
- Bundle directories must end in `.activity` for Sugar's auto-discovery.
  The symlink target doesn't need the suffix, but the symlink name does.
- Activity icons follow a naming convention: `<icon-name>-72.svg` (72px)
  and `<icon-name>-100.svg` (100px). The `icon` field in `activity.info`
  is the base name without suffix.
- The `exec = sugar-activity3` launcher expects the activity to define a
  callable (function or class constructor) in its `__init__.py`. For
  GTK4 toolkit activities, `exec = sugar-activity4` uses the same
  convention but imports from `sugar4.activity.activityfactory` instead.
