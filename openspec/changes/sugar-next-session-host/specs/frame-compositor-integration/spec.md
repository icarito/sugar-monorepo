# frame-compositor-integration — Delta Spec

## ADDED Requirements

### Requirement: Frame reads window state from Hyprland IPC
When running under Hyprland, the Frame's running-apps list SHALL be derived
from `hyprctl clients -j` JSON output. An entry SHALL appear when a mapped
client with a recognized app_id exists and SHALL disappear when no mapped
client with that app_id remains.

#### Scenario: App appears in Frame on launch
- **WHEN** an app is launched (from the shell or externally via a terminal)
  and a Hyprland client window appears with a non-empty `class`
- **THEN** the Frame's running list includes that app within one polling
  interval

#### Scenario: App disappears from Frame on close
- **WHEN** an app's last Hyprland client window closes
- **THEN** the Frame's running list no longer includes that app within one
  polling interval

### Requirement: Frame focus tracks Hyprland active window
The shell's focused-app state SHALL track the Hyprland `activewindow` as
reported by `hyprctl activewindow -j`. When the active window changes, the
`app_state.set_focused()` method SHALL be called with the new window's
class (app_id).

#### Scenario: Focus follows window activation
- **WHEN** the learner switches focus between two tiled windows (via
  keyboard or click)
- **THEN** the Frame and icon rendering reflect the newly-focused app

### Requirement: Frame switching dispatches to Hyprland
Clicking a running entry in the Frame SHALL bring that app's window to the
front by issuing `hyprctl dispatch focuswindow` with the client's class
identifier.

#### Scenario: Frame click activates app window
- **WHEN** the learner clicks a running app's Frame entry
- **THEN** that app's window is focused in the Hyprland session and the
  Frame closes

### Requirement: Frame does not duplicate the Hyprland stripe
The Frame SHALL render as a floating overlay showing running apps and view
switching controls. It SHALL NOT attempt to render a workspace bar, system
tray, clock, or other elements that belong to the compositor's native
stripe/bar. The stripe SHALL remain Hyprland's responsibility.

#### Scenario: Frame coexists with Hyprland bar
- **WHEN** the Hyprland session has a configured bar/stripe showing
  workspaces and a clock
- **THEN** Sugar Next's Frame overlays on top showing only running apps and
  view switcher, without duplicating workspace or clock widgets
