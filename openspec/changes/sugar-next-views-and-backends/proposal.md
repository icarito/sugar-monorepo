## Why

Two threads of work landed on the parallel `icarito/sugar-next` branch
while `sugar-next-next` was being archived here, and neither belongs in an
already-archived change:

1. **Views as views.** Treating desktop-grid, app-grid, and search-first as
   interchangeable *layouts* selected from a Settings panel was a design
   mistake. Choosing how you see your system is a *navigation* concern, not
   a configuration one — Sugar classic had this right with its four views.
   These become **views** the learner navigates from the Frame (F1/F2/F3),
   and the Settings layout selector is removed. This supersedes the
   Settings-based layout selector shipped by `sugar-next-next`.

2. **Extension language backends.** The extension contract is now fully
   documented (`extension-contract.md`). This change formalises the *new*
   parts: non-Python backends via a subprocess JSON/stdio protocol (gjs
   first, then any executable), and a launch-cancel return contract.

Both need runtime implementation, so they warrant an active change rather
than being buried in the archive.

## What Changes

- Re-ground the three Home View layouts as Frame-navigated **views**
  (Desktop/Apps/Search), each remembering its own state, with F1/F2/F3
  direct keybindings and a view switcher in the Frame overlay bar.
- Remove the Home View layout selector from the Settings panel and retire
  the `HomeViewLayout` interface once views land.
- Add non-Python extension backends: a gjs subprocess backend and a generic
  subprocess backend, both speaking a line-delimited JSON protocol.
- Add the `on_app_launch` launch-cancel return contract (`{"cancel": true}`).

## Impact

- **Supersedes** the archived `sugar-next-next` Settings layout selector
  (sections 2.6 and the polish pass): the layout dropdown is removed in
  favour of Frame navigation. The shell's existing layout widgets are
  reused as view content.
- New capabilities: `frame-views` (view navigation) and additive
  requirements on `extensions` (backends, launch-cancel).
- Reference: `extension-contract.md` in this change carries the full,
  already-agreed extension contract as design context.
