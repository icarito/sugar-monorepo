# Sugar Next — Tasks

## Fase 1: Shell mínimo + App Grid

- [ ] **1.1** Create `sugar-next/` directory structure under monorepo root
- [ ] **1.2** Write `shell/main.py` — minimal GTK4 app that opens a window
- [ ] **1.3** Write `bundles/desktop-bundle.py` — wrapper for `.desktop` files
- [ ] **1.4** Write `shell/app-grid.py` — `Gtk.FlowBox` listing apps from XDG
- [ ] **1.5** Wire launch: click icon → `Gio.AppInfo.launch()`
- [ ] **1.6** Add search bar filtering
- [ ] **1.7** Add `pyproject.toml` for `sugar-next/` as installable Python package
- [ ] **1.8** Smoke test: shell starts, shows apps, clicking launches Firefox

## Fase 2: API de extensiones

- [ ] **2.1** Design hook interface (start with `on_app_launch`)
- [ ] **2.2** Write `api/hooks.py` — scanner + caller for extension `.py` files
- [ ] **2.3** Write 2 example extensions (logger, launcher-counter)
- [ ] **2.4** Wire hooks into the app launch pipeline
- [ ] **2.5** Document the extension API in `specbook/docs/`

## Fase 3: Frame universal

- [ ] **3.1** Design Frame widget (icons, hot-corner, keybinding)
- [ ] **3.2** Write `shell/frame.py` — basic window switcher
- [ ] **3.3** Integrate with app grid: "Pin to Frame favorites"
- [ ] **3.4** Per-window palette (placeholder actions)

## Fase 4: Journal opt-in + packaging

- [ ] **4.1** Design Journal extension API
- [ ] **4.2** Write Journal extension (SQLite backend)
- [ ] **4.3** Create Nix flake for self-contained build
- [ ] **4.4** Create OCI image for `podman run`
- [ ] **4.5** Write `bootstrap.sh` — one-command setup on any distro
- [ ] **4.6** Write documentation + demo video

## Community

- [ ] **C.1** Post to sugar-devel with demo and proposal
- [ ] **C.2** Post to IAEP with educational framing
- [ ] **C.3** Reach out to Walter Bender for feedback
