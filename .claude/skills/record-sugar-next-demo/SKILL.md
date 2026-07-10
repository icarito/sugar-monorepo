---
name: record-sugar-next-demo
description: Use when the user wants a demo video/recording of the Sugar Next shell (sugar-next/) — a scripted, no-manual-input tour of Desktop/pie menu, Apps view, Frame, and Settings, rendered to an mp4.
metadata:
  author: sugarlabs-specbook
  version: "1.0"
---

# Record Sugar Next Demo

Generates a short (~25s) mp4 walkthrough of the Sugar Next shell —
Desktop pie menu, Apps view, pin/unpin, Frame, Settings — with zero
manual input (no mouse/keyboard driving needed, no screen-recorder UI to
click through).

## How it works

- `demo_driver.py` launches `SugarShell` and drives it entirely through
  the app's own Python methods (`_activate_view`, `pie_menu.pin_favorite`,
  `frame.reveal`, `_on_settings_requested`, …) on a `GLib.timeout_add`
  schedule — no `xdotool`/synthetic input needed. It also overlays a
  bottom-center caption box per beat (matching the style of the
  hand-made `demo.mp4` this skill's method was reverse-engineered from).
- `record.sh` launches the driver with `GDK_BACKEND=x11` (forces a real
  X11 window even under a Wayland session, via XWayland), locates that
  window with `xwininfo`, and captures it with `ffmpeg -f x11grab
  -window_id …` for the driver's lifetime. The driver exits on its own
  once the scripted sequence finishes, which stops the recording.

## Why x11grab, not the Wayland screencast portal

GNOME's native screen recorder (`Ctrl+Shift+Alt+R`) and the
`org.freedesktop.portal.ScreenCast` API both require **interactive user
consent** (a picker dialog) — by design, so an unattended process can't
silently record the screen. `x11grab` captures an X11 window directly
and has no such prompt, which is what makes an unattended/scripted
recording possible at all.

**This is a real capability, not just a technical detail** — get
explicit confirmation from the user for the current session before
running `record.sh` unattended. Don't assume a prior "you did this
before" is blanket authorization; confirm each time this skill is
invoked, the same way you would before any action that bypasses a
security consent step.

## Usage

```bash
cd .claude/skills/record-sugar-next-demo
./record.sh                       # saves to ~/sugar-next-demo-<timestamp>.mp4
./record.sh /path/to/output.mp4   # explicit output path
```

Requires `ffmpeg` and `xwininfo` (both already on this workspace's dev
machine). Does not need `xdotool` or `wf-recorder`.

The script resets `~/.config/sugar-next/settings.json` and
`~/.local/share/sugar-next/favorites.json` first, so the demo always
starts from a clean Desktop view with no favorites pinned — matching the
narration in `demo_driver.py`.

## Editing the script

The beat sequence lives in `build_default_script()` in `demo_driver.py`
— each `driver.add(caption_text, delay_ms, action_fn)` call is one beat.
`action_fn=None` just holds the current caption/state (used to dismiss a
popover after showing it). Edit beats there and re-run `record.sh`; no
other file needs to change.

## Known gotcha this skill's setup ran into

`Gtk.Fixed` subclasses in this GTK4/PyGObject environment do **not**
reliably call an overridden `do_size_allocate` — child layout goes
through the internal `GtkFixedLayout`, not the widget's own vfunc, so a
`Gtk.Fixed`-based widget (like `sugar_next/shell/pie_menu.py`) that
repositions its children in `do_size_allocate` will silently never
reflow after its first (often 0×0) allocation. Confirmed with a minimal
reproduction outside Sugar Next entirely (plain `Gtk.Fixed` subclass,
`do_size_allocate` override never fires even under a live `Gtk.Window`).
Fix: use `Gtk.Widget.add_tick_callback()` instead — it fires every frame
and naturally converges to the real size within a frame or two of
mapping. If you touch `pie_menu.py`'s layout code, keep using the tick
callback pattern (see `_on_tick` in that file) rather than reintroducing
a `do_size_allocate` override.
