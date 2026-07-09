# Community outreach drafts (tasks C.1–C.3)

Drafts for Sebastian to review, edit, and send. Attach the demo video and
link to the repo (github.com/icarito/sugar-monorepo, `sugar-next/`).

---

## C.1 — sugar-devel

**Subject:** Sugar Next: a modern, self-contained pipeline for Sugar (demo inside)

Hi all,

I've been prototyping something I'd like to share: **Sugar Next**, a
sibling project (not a fork, not a replacement) exploring what a Sugar
shell could look like on today's stack.

What works today (demo video attached):

- A GTK4 shell that runs as a normal Wayland client on any current distro.
- An App Grid showing *all* the system's applications (XDG .desktop
  entries) — activities and system apps coexist, no isolation bubble.
- Instant search, click to launch.
- A Frame overlay (F6 / hot corner) with pinned favorites and
  session-launched apps, with per-item palettes.
- An extension API with a deliberately low floor: drop a plain `.py` file
  in `~/.local/share/sugar-next/extensions/` — no GObject, no D-Bus, no
  build system. A working extension is ~5 lines.
- An opt-in Journal, implemented *as* an extension (SQLite, no D-Bus
  service).
- `pip install` + a Containerfile; bootstraps on any Linux in one command.

Just as important, what it does **not** do: it doesn't touch the `sugar`
repo, jarabe, the GTK3 toolkit, or PR #1019. The legacy stack stays
exactly as it is. Sugar Next is a place to experiment with lower barriers
— for contributors and for kids writing their first extension.

Code and specs: <repo link>. Feedback very welcome, especially on the
extension API direction (next up: Zeitgeist as a Journal event source and
wlr-foreign-toplevel-management for true window management in the Frame).

Saludos,
Sebastian

---

## C.2 — IAEP (educational framing)

**Subject:** Lowering the floor again: a Sugar Next prototype

Hi all,

Sugar's founding insight was the low floor: a child could look inside and
change things. On the current stack, "looking inside" means GObject
Introspection, D-Bus, Autotools — a floor that has quietly risen out of
reach.

Sugar Next is a prototype that lowers it back down. A learner writes
five lines of Python in a text file, drops it in a folder, restarts the
shell — and their code runs every time any app launches. No compiler, no
build system, no framework. The Journal itself is written that way: it's
an extension a learner could read in one sitting (60 lines) and modify.

It also ends the isolation bubble: the shell shows the whole computer —
Firefox, GIMP, the terminal — not only XO activities. Kids graduate from
using their computer to programming it, one hook at a time.

Demo video attached; technical details on sugar-devel.

Saludos,
Sebastian

---

## C.3 — Walter Bender (direct note)

Subject: A prototype you might enjoy: Sugar Next

Walter,

I built a small prototype I'd value your eyes on before I take it any
further: a GTK4 Sugar-inspired shell where the extension floor is five
lines of Python, the Journal is opt-in (and itself just an extension),
and system apps share the grid with activities.

It deliberately doesn't touch jarabe or the toolkit — it's a sibling
experiment, not a successor claim. But the design questions are the ones
you've thought about longest: what's the minimum a child needs to know to
change their computer? Is an opt-in Journal still a Journal?

Two-minute demo attached. I'd love your reaction, critical or otherwise.

Sebastian
