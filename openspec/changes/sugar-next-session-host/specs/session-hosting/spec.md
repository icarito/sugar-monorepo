# session-hosting — Delta Spec

## ADDED Requirements

### Requirement: Shell detects and integrates with Hyprland session
The shell SHALL, when `HYPRLAND_INSTANCE_SIGNATURE` is present in the
environment, source window and focus state from Hyprland IPC rather than
from a separate toplevel-tracking protocol client.

#### Scenario: Hyprland session detected at startup
- **WHEN** the shell starts and `HYPRLAND_INSTANCE_SIGNATURE` is set
- **THEN** the shell skips `TopLevelTracker.start()` and initializes the
  Hyprland IPC module instead

#### Scenario: Non-Hyprland session falls back
- **WHEN** the shell starts and `HYPRLAND_INSTANCE_SIGNATURE` is NOT set
- **THEN** the shell uses the existing `TopLevelTracker` path unchanged

### Requirement: Apps launched from the shell open inside the session
Apps launched from the Home View (grid, pie menu) SHALL render as regular
Hyprland clients subject to the configured tiling layout.

#### Scenario: Launch from grid creates a tiled window
- **WHEN** the learner activates an app from the App Grid
- **THEN** the app's window appears in the Hyprland tiling layout and its
  entry appears in the Frame's running list

### Requirement: Shell prefers layer-shell for its root surface
When GTK layer-shell GI bindings are available, the shell SHALL initialize
its main window as a layer-shell surface anchored to all output edges rather
than relying on a compositor-managed `xdg_toplevel` window.

#### Scenario: Layer-shell binding is available
- **WHEN** Sugar Next starts and a supported GTK layer-shell namespace can
  be loaded
- **THEN** the main shell window is initialized with layer-shell before it
  is presented

#### Scenario: Layer-shell binding is absent
- **WHEN** Sugar Next starts without a supported GTK layer-shell namespace
- **THEN** startup continues as an `xdg_toplevel` and the Hyprland window
  rules provide the fullscreen fallback

### Requirement: Standalone session entry is documented
The project SHALL document a session entry file (`sugar-next.desktop`)
suitable for `/usr/share/wayland-sessions/` specifying Hyprland as the
compositor with a config that autostarts Sugar Next from the
`hyprland.start` event via `hl.exec_cmd()`.

#### Scenario: Login manager lists Sugar Next
- **WHEN** the documented `sugar-next.desktop` is placed in
  `/usr/share/wayland-sessions/`
- **THEN** the login manager offers "Sugar Next" as a session choice that
  starts Hyprland with Sugar Next as the shell
