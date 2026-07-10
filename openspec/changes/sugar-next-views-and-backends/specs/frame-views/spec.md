## Views as views — not Settings

The current Home View layout system treats desktop-grid, app-grid, and
search-first as interchangeable *layouts* toggled in a Settings panel.
This was a design mistake: layouts are a low-level widget concern, but
choosing between fundamentally different ways of seeing your system is a
*navigation* concern. Sugar classic had this right with its four views
(Neighborhood, Groups, Home, Activity).

This spec re-grounds the three layouts as distinct **views** the learner
navigates between via the Frame, not via Settings.

---

## ADDED Requirements

### Requirement: Views accessible from the Frame

The shell SHALL provide three views — Desktop, Apps, Search — accessible
from the Frame (overlay bar at screen bottom / F6), NOT from Settings.
The Frame SHALL show a view switcher alongside running windows and
favorites.

#### Scenario: Switching from Desktop to Apps view
- **WHEN** the learner presses F6 (Frame) and selects the "Apps" button
- **THEN** the shell switches to the App Grid view. The Frame closes.
  The same view is active next time the Frame is opened.

#### Scenario: Frame shows running windows AND view switcher
- **WHEN** the Frame opens (F6 or hot corner)
- **THEN** it shows: [Desktop] [Apps] [Search] buttons on the left,
  running windows in the center, pinned favorites on the right

### Requirement: Settings loses layout selector

The Settings panel SHALL NOT include a Home View layout selector. The
learner changes views through the Frame, never through a configuration
panel.

#### Scenario: Settings no longer shows layout option
- **WHEN** the learner opens Settings
- **THEN** the Background, Accent color, Contrast, Extensions, and About
  sections are present, but there is no layout selector

### Requirement: Each view remembers its state

Each view SHALL preserve its scroll position, search text, and filter
state when the learner switches away and back.

#### Scenario: Switching views preserves scroll
- **WHEN** the learner scrolls down in Apps view, switches to Desktop,
  then switches back to Apps
- **THEN** the Apps view shows the same scroll position as before

### Requirement: Desktop view shows background

The Desktop view (F1 as direct keybinding) SHALL display app icons
floating on the user's chosen background image. Container folders expand
into sub-grids.

#### Scenario: Desktop background
- **WHEN** the learner has set a background image in Settings
- **THEN** the Desktop view shows icons over that image

### Requirement: Apps view is the grid

The Apps view (F2 direct keybinding) SHALL display the App Grid
(Gtk.FlowBox with search bar, no background image).

#### Scenario: Apps filtered by search
- **WHEN** the learner types in the search bar in Apps view
- **THEN** the grid filters in real time

### Requirement: Search view is blank until typed

The Search view (F3 direct keybinding) SHALL show no icons until the
learner types in the search bar.

#### Scenario: Empty Search view
- **WHEN** the Search view is active and the search bar is empty
- **THEN** no app icons are visible

### Requirement: Default view on first start

The shell SHALL start in Desktop view on first launch. Returning learners
see the last active view (persisted in config).

#### Scenario: First launch
- **WHEN** the shell starts for the first time
- **THEN** Desktop view is shown

#### Scenario: Subsequent launch
- **WHEN** the shell starts and a view was previously selected
- **THEN** that same view is shown
