# Sugar Next — A Learning Shell for Everyday Computing

## Problem

Sugar Labs has a rich legacy of educational software, but the main desktop
environment (Sugar shell / jarabe) is built on a stack that is increasingly
hard to maintain and extend:

- **GTK3 + X11** — both deprecated upstream. The GTK4 port of the shell
  (PR #1019) stalled on environment friction, not technical difficulty.
- **Autotools build system** — unfamiliar to modern contributors.
- **Activities-only model** — the shell only shows XO-style bundles.
  System applications (Firefox, terminal, GIMP) are invisible, isolating
  users from the rest of their computer.
- **High barrier for creators** — writing a Sugar activity requires knowing
  GObject Introspection, activity lifecycle, D-Bus, and the build system.
- **No reproducible dev environment** — the recommended setup is a 1 GB
  Live ISO, which itself depends on a specific distro version.

Meanwhile, the community is active (GSoC 2026 had many participants) but
all energy goes into maintaining the existing stack rather than evolving it.

## Proposal

Create **Sugar Next** — a new project within Sugar Labs that provides a
fast, modern, self-contained pipeline for building a computing environment
that respects the user. Sugar Next is **not a fork** of the Sugar shell;
it is a **sibling project** that coexists with the legacy stack.

Key traits:
- **Activities and system apps coexist** — no isolation bubble.
- **Low floor for creators** — write an extension in ~10 lines of Python,
  no GObject knowledge required.
- **Self-contained and self-hosted** — runs anywhere via pip + OCI.
- **Opt-in, not imposed** — Journal, collaboration, activity model are all
  optional layers, not mandatory.

## Relationship to existing Sugar

| Component | Relationship |
|-----------|-------------|
| `sugar` (jarabe shell) | Independent. Sugar Next has its own minimal shell. |
| `sugar-toolkit-gtk3` | Untouched. For legacy activities. |
| `sugar-toolkit-gtk4` | Inspiration for APIs, but no compatibility burden. |
| XO activities | Runnable via compat layer if desired. |
| Journal | Clean reimplementation, opt-in. |
| Frame | Clean reimplementation as universal nexus. |

## Success criteria

1. A GTK4 shell starts and displays an App Grid with system applications.
2. Clicking an app icon launches it via `Gio.AppInfo.launch()`.
3. An extension API exists: write a `.py` file in `~/.local/share/sugar-next/extensions/`,
   hook into `on_app_launch`, and it works.
4. The entire environment can be bootstrapped with `pip install` on any Linux
   distro.

## Non-goals

- Replacing the `sugar` repo or its PR #1019.
- Migrating existing XO activities to the new API.
- Redesigning SnowflakeLayout or any jarabe-specific layout.
- Implementing legacy mesh collaboration (local XO mesh is dead technology).

## Risks

- **Community resistance** — some may see Sugar Next as a threat to the
  legacy shell. Mitigation: frame it as a sibling project, keep the
  `sugar` repo untouched.
- **Scope creep** — it's tempting to solve everything at once.
  Mitigation: strictly follow the OpenSpec change cycle, one small change
  at a time.
- **Underestimating the extension API** — a good extension API is hard to
  design. Mitigation: start with one simple hook (`on_app_launch`), add
  more based on real usage.
