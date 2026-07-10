-- Minimal Hyprland config for developing Sugar Next in a nested window.
--
-- Sugar Next autostarts inside this session so the shell + Frame can be
-- developed against a real tiling compositor with working zwlr_foreign_
-- toplevel_manager_v1 (open/close/focus events).
--
-- Hyprland 0.55+ uses Lua. See dev/run-hyprland-nested.sh.
--
-- Verified on Hyprland 0.55.4 (Arch).

local function shquote(value)
    return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end

-- Sugar Next autostart (shell + Frame + Hyprland IPC)
local project_dir = os.getenv("SUGAR_NEXT_PROJECT_DIR") or os.getenv("PWD") or "."
local python = os.getenv("SUGAR_NEXT_PYTHON") or "python3"
local nested_size = os.getenv("SUGAR_NEXT_NESTED_SIZE") or "1024x640"
local nested_scale = os.getenv("SUGAR_NEXT_NESTED_SCALE") or "1"
local layer_shell_preload = os.getenv("SUGAR_NEXT_LAYER_SHELL_PRELOAD")
local env_prefix = ""
if layer_shell_preload and layer_shell_preload ~= "" then
    env_prefix = "LD_PRELOAD=" .. shquote(layer_shell_preload) .. " "
end

local sugar_next_cmd = "cd " .. shquote(project_dir)
    .. " && PYTHONPATH=" .. shquote(project_dir)
    .. " " .. env_prefix .. shquote(python) .. " -m sugar_next.shell.main"

hl.on("hyprland.start", function()
    hl.exec_cmd(sugar_next_cmd)
end)

-- Virtual output at a comfortable dev size
hl.monitor({
    output = "",
    mode = nested_size .. "@60",
    position = "0x0",
    scale = nested_scale,
})

-- Dwindle tiling with gaps — the default Hyprland feel
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
        kb_layout = "us,es",
        kb_options = "grp:alt_shift_toggle",
        follow_mouse = 1,
    },
})

-- Treat Sugar Next as the session surface, not as one tiled app among
-- others. A real layer-shell root surface can come later; this keeps the
-- current GTK app behaving like the shell while we stay dependency-free.
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

-- Super + Q to close focused window
hl.bind(main_mod .. " + Q", hl.dsp.window.close())

-- Super + F to toggle fullscreen
hl.bind(main_mod .. " + F", hl.dsp.window.fullscreen())

-- Super + Return to open kitty terminal
hl.bind(main_mod .. " + Return", hl.dsp.exec_cmd("kitty"))

-- Super + Space to toggle floating
hl.bind(main_mod .. " + Space", hl.dsp.window.float({ action = "toggle" }))

-- Move focus with Super + arrows
hl.bind(main_mod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(main_mod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(main_mod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(main_mod .. " + down", hl.dsp.focus({ direction = "down" }))
