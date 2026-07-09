# Sugar Next — Tasks

## Fase 1: Shell mínimo + App Grid

- [x] **1.1** Create `sugar-next/` directory structure under monorepo root
- [x] **1.2** Write `shell/main.py` — minimal GTK4 app that opens a window
- [x] **1.3** Write `bundles/desktop-bundle.py` — wrapper for `.desktop` files
- [x] **1.4** Write `shell/app-grid.py` — `Gtk.FlowBox` listing apps from XDG
- [x] **1.5** Wire launch: click icon → `Gio.AppInfo.launch()`
- [x] **1.6** Add search bar filtering
- [x] **1.7** Add `pyproject.toml` for `sugar-next/` as installable Python package
- [x] **1.8** Smoke test: shell starts, shows apps, clicking launches Firefox

## Fase 2: API de extensiones

- [x] **2.1** Design hook interface (start with `on_app_launch`)
- [x] **2.2** Write `api/hooks.py` — scanner + caller for extension `.py` files
- [x] **2.3** Write 2 example extensions (logger, launcher-counter)
- [x] **2.4** Wire hooks into the app launch pipeline
- [x] **2.5** Document the extension API in `specbook/docs/`

## Fase 3: Frame universal

- [x] **3.1** Design Frame widget (icons, hot-corner, keybinding)
- [x] **3.2** Write `shell/frame.py` — basic window switcher
- [x] **3.3** Integrate with app grid: "Pin to Frame favorites"
- [x] **3.4** Per-window palette (placeholder actions)

## Fase 4: Journal opt-in + packaging

- [x] **4.1** Design Journal extension API
- [x] **4.2** Write Journal extension (SQLite backend)
- [x] **4.3** Create OCI image for `podman run`
- [x] **4.4** Write minimal `bootstrap.sh` — `pip install` + `.desktop` entry
- [x] **4.5** Write documentation + demo video (README + extension API doc + `sugar-next/docs/demo.mp4`)

## Community

- [ ] **C.1** Post to sugar-devel with demo and proposal
- [ ] **C.2** Post to IAEP with educational framing
- [ ] **C.3** Reach out to Walter Bender for feedback
