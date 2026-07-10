#!/usr/bin/env gjs
// Example extension (JavaScript / gjs backend).
//
// The shell spawns this file per event and sends one JSON object on
// stdin: {"event": "on_app_launch", "args": {"a0": "firefox.desktop"}}.
// It must reply with one JSON object on stdout: {"ok": true}, or
// {"cancel": true} to veto an on_app_launch, or {"error": "..."}.
//
// Install by copying into ~/.local/share/sugar-next/extensions/ and
// making it executable is optional — the .js suffix routes it to gjs.

const GLib = imports.gi.GLib;

function readStdin() {
    const stdin = imports.gi.Gio.UnixInputStream.new(0, false);
    const data = imports.gi.Gio.DataInputStream.new(stdin);
    const [line] = data.read_line(null);
    return line ? imports.byteArray.toString(line) : '';
}

function main() {
    let message;
    try {
        message = JSON.parse(readStdin());
    } catch (e) {
        print(JSON.stringify({ error: `bad input: ${e}` }));
        return;
    }

    if (message.event === 'on_app_launch') {
        const appId = message.args.a0 || '(unknown)';
        printerr(`[logger.js] launching ${appId}`);
    } else if (message.event === 'on_shell_start') {
        printerr('[logger.js] Sugar Next shell started');
    }

    // Acknowledge. Return {cancel: true} here to block a launch.
    print(JSON.stringify({ ok: true }));
}

main();
