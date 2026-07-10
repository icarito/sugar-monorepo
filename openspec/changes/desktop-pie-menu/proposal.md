# Desktop Pie Menu — rethink Desktop view, simplify Frame

## What

Replace the current Desktop grid view (icons floating on wallpaper) with a
**radial pie menu** of pinned favorites on the wallpaper. Move Settings
into the pie menu center. Remove Search view. Simplify the Frame.

## Why

The Desktop grid and App grid were redundantly similar (both show icons in
a grid). Desktop view should be distinct: a personal, minimal space with
only the learner's pinned favorites, accessible as a radial menu. The
Frame becomes a view switcher + running windows, not a catch-all.

## Scope

- Replace `desktop_grid.py` with a pie menu widget showing favorites
- Move Settings button from Frame into the pie menu center
- Remove Search view
- Remove favorites section from Frame
- Reserve F3 for future Groups/Neighborhood view

## Non-goals

- Redesign Apps view (stays as-is)
- Implement Groups/Neighborhood (F3 is reserved, not implemented)
- Change the extension API or hooks
