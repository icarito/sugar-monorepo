-- Sugar Next standalone Hyprland session template.
--
-- Install a display-manager entry such as:
--   /usr/share/wayland-sessions/sugar-next.desktop
-- with:
--   [Desktop Entry]
--   Name=Sugar Next
--   Comment=Sugar Next learning shell on Hyprland
--   Exec=Hyprland -c /etc/sugar-next/hyprland.lua
--   Type=Application
--
-- Native sessions should not set AQ_BACKENDS. That variable is only for
-- nested development via dev/run-hyprland-nested.sh.
--
-- Python/PyGObject launches may need gtk4-layer-shell's preload helper so
-- libgtk4-layer-shell is loaded before libwayland:
--   LD_PRELOAD=/usr/lib/liblayer-shell-preload.so sugar-next

hl.on("hyprland.start", function()
    hl.exec_cmd(
        "if [ -r /usr/lib/liblayer-shell-preload.so ]; then "
        .. "LD_PRELOAD=/usr/lib/liblayer-shell-preload.so sugar-next; "
        .. "else sugar-next; fi"
    )
end)

hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = "auto",
})

hl.config({
    general = {
        gaps_in = 5,
        gaps_out = 10,
        border_size = 2,
        layout = "dwindle",
    },
    decoration = {
        rounding = 6,
    },
    input = {
        follow_mouse = 1,
    },
})

hl.workspace_rule({
    workspace = "1",
    gaps_in = 0,
    gaps_out = 0,
    border_size = 0,
    no_rounding = true,
})

hl.window_rule({
    name = "sugar-next-shell",
    match = { class = "org.sugarlabs.SugarNext" },

    fullscreen = true,
    border_size = 0,
    rounding = 0,
})

local main_mod = "SUPER"

hl.bind(main_mod .. " + Q", hl.dsp.window.close())
hl.bind(main_mod .. " + F", hl.dsp.window.fullscreen())
hl.bind(main_mod .. " + Return", hl.dsp.exec_cmd("kitty"))
hl.bind(main_mod .. " + Space", hl.dsp.window.float({ action = "toggle" }))
hl.bind(main_mod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(main_mod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(main_mod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(main_mod .. " + down", hl.dsp.focus({ direction = "down" }))
