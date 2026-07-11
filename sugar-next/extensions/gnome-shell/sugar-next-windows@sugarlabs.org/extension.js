import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const BUS_NAME = 'org.sugarlabs.SugarNext.WindowSource';
const OBJECT_PATH = '/org/sugarlabs/SugarNext/WindowSource';

const INTERFACE_XML = `
<node>
  <interface name="org.sugarlabs.SugarNext.WindowSource">
    <method name="FocusWindow">
      <arg type="s" direction="in" name="app_id"/>
      <arg type="b" direction="out" name="success"/>
    </method>
    <method name="ListWindows">
      <arg type="a(ss)" direction="out" name="windows"/>
    </method>
    <method name="GetFocused">
      <arg type="s" direction="out" name="app_id"/>
    </method>
    <signal name="WindowOpened">
      <arg type="s" name="app_id"/>
      <arg type="s" name="title"/>
    </signal>
    <signal name="WindowClosed">
      <arg type="s" name="app_id"/>
    </signal>
    <signal name="WindowFocused">
      <arg type="s" name="app_id"/>
    </signal>
  </interface>
</node>`;

// Sugar Next's shell-startup design (window-observation spec) needs one
// data source per supported startup mode. In a GNOME-hosted session there
// is no protocol equivalent to wlr-foreign-toplevel-management (Mutter
// does not implement it, by design), so this extension is that source:
// it watches Mutter's own window list from inside GNOME Shell — the one
// process with unrestricted access to it — and republishes open/close/
// focus events on the session bus for sugar_next/shell/gnome_window_source.py
// to consume. It is also how the shell's window-management code (Frame
// running list, focus-follow) gets exercised against real desktop data
// while developing, without a nested compositor.
export default class SugarNextWindowSourceExtension extends Extension {
    enable() {
        this._display = global.display;
        this._windowIds = new Map(); // MetaWindow -> unmanaged signal id
        this._dbusImpl = Gio.DBusExportedObject.wrapJSObject(INTERFACE_XML, this);
        this._dbusImpl.export(Gio.DBus.session, OBJECT_PATH);
        this._nameOwnerId = Gio.bus_own_name(
            Gio.BusType.SESSION,
            BUS_NAME,
            Gio.BusNameOwnerFlags.NONE,
            null,
            null,
            null,
        );

        this._windowCreatedId = this._display.connect('window-created', (_display, win) => {
            this._watchWindow(win);
            this._pendingOpen ??= new Set();
            this._pendingOpen.add(win);
            this._emitOpenedWhenReady(win);
        });

        this._focusId = this._display.connect('notify::focus-window', () => {
            const win = this._display.focus_window;
            this._dbusImpl.emit_signal(
                'WindowFocused',
                new GLib.Variant('(s)', [win ? win.get_wm_class() ?? '' : '']),
            );
        });

        for (const actor of global.get_window_actors()) {
            const win = actor.get_meta_window();
            this._watchWindow(win);
        }
    }

    _watchWindow(win) {
        if (this._windowIds.has(win))
            return;
        const id = win.connect('unmanaged', () => {
            this._windowIds.delete(win);
            this._pendingOpen?.delete(win);
            this._dbusImpl.emit_signal(
                'WindowClosed',
                new GLib.Variant('(s)', [win.get_wm_class() ?? '']),
            );
        });
        this._windowIds.set(win, id);
    }

    // window-created fires when Mutter creates the MetaWindow object, but
    // wm_class/title arrive asynchronously from the client afterward — a
    // naive read here reliably returns empty strings (verified live: every
    // WindowOpened emitted '', '' while WindowClosed on the same window
    // moments later had the real wm_class). Neither 'notify::wm-class' nor
    // the compositor actor's 'first-frame' reliably fired in live testing
    // on GNOME Shell 50, and a tight GLib.idle_add retry loop (near-zero
    // spacing) still saw it empty after 50 iterations — rather than depend
    // on an exact Mutter signal that may vary by version, poll on a real
    // 100ms timer up to 2s, which reliably observes the populated value.
    _emitOpenedWhenReady(win, attempt = 0) {
        // Closed before wm_class ever populated (e.g. a very short-lived
        // helper window) — _watchWindow's 'unmanaged' handler already
        // removed it from _pendingOpen; nothing to report.
        if (!this._pendingOpen?.has(win))
            return;
        const wmClass = win.get_wm_class();
        if (wmClass) {
            this._pendingOpen.delete(win);
            this._emitOpened(win, wmClass);
            return;
        }
        if (attempt >= 20) {
            // 20 x 100ms = 2s without wm_class populating — give up
            // rather than poll forever; emit what we have so the shell
            // still sees *a* WindowOpened event for this window.
            this._pendingOpen.delete(win);
            this._emitOpened(win, '');
            return;
        }
        // idle_add alone reruns near-instantly (sub-millisecond) and
        // consistently observed wm_class still empty after 50 iterations
        // — a real 100ms spacing gives the client's property update time
        // to land, matching the ~1s gap observed before WindowFocused
        // picked up the correct value on the same window.
        GLib.timeout_add(GLib.PRIORITY_DEFAULT, 100, () => {
            this._emitOpenedWhenReady(win, attempt + 1);
            return GLib.SOURCE_REMOVE;
        });
    }

    _emitOpened(win, wmClass) {
        this._dbusImpl.emit_signal(
            'WindowOpened',
            new GLib.Variant('(ss)', [wmClass, win.get_title() ?? '']),
        );
    }

    // D-Bus method: ListWindows() -> a(ss)
    ListWindows() {
        const windows = [];
        for (const actor of global.get_window_actors()) {
            const win = actor.get_meta_window();
            const wmClass = win.get_wm_class();
            if (wmClass) {
                windows.push([wmClass, win.get_title() ?? '']);
            }
        }
        return windows;
    }

    // D-Bus method: GetFocused() -> s
    GetFocused() {
        const win = this._display.focus_window;
        return win ? (win.get_wm_class() ?? '') : '';
    }

    // D-Bus method: FocusWindow(app_id) -> bool
    FocusWindow(appId) {
        // Normalize: strip optional ".desktop" suffix and lowercase so a
        // desktop-file id from the bundle matches the compositor's WM_CLASS.
        const wanted = appId.replace(/\.desktop$/i, "").toLowerCase();
        for (const actor of global.get_window_actors()) {
            const win = actor.get_meta_window();
            const wmClass = (win.get_wm_class() || "").toLowerCase();
            if (wmClass === wanted) {
                win.activate(global.get_current_time());
                return true;
            }
        }
        return false;
    }

    disable() {
        for (const [win, id] of this._windowIds)
            win.disconnect(id);
        this._windowIds.clear();
        this._pendingOpen?.clear();
        this._pendingOpen = null;

        if (this._windowCreatedId) {
            this._display.disconnect(this._windowCreatedId);
            this._windowCreatedId = null;
        }
        if (this._focusId) {
            this._display.disconnect(this._focusId);
            this._focusId = null;
        }
        if (this._nameOwnerId) {
            Gio.bus_unown_name(this._nameOwnerId);
            this._nameOwnerId = null;
        }
        if (this._dbusImpl) {
            this._dbusImpl.unexport();
            this._dbusImpl = null;
        }
        this._display = null;
    }
}
