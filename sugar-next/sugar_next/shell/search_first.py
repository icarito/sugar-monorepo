"""Search-first Home View layout.

A blank canvas with a search bar. No app icons are visible until the
learner types — minimal distraction, full focus.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gtk, Pango



class _ResultRow(Gtk.Box):
    def __init__(self, bundle, on_activate, icon_size=32):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.add_css_class("search-result-row")
        self.bundle = bundle
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        icon = bundle.icon
        image = (
            Gtk.Image.new_from_gicon(icon)
            if icon
            else Gtk.Image.new_from_icon_name("application-x-executable")
        )
        image.set_pixel_size(icon_size)
        self.append(image)

        label = Gtk.Label(label=bundle.name)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_xalign(0)
        self.append(label)

        click = Gtk.GestureClick()
        click.connect("pressed", lambda *_: on_activate(bundle))
        self.add_controller(click)


class SugarSearchFirst(Gtk.Box):
    __gtype_name__ = "SugarNextSearchFirst"

    view_id = "search-first"
    view_name = "Search"

    _CSS = """
        .search-result-row {
            border-radius: 10px;
            padding: 6px 8px;
            background: linear-gradient(180deg,
                var(--sn-surface) 0%,
                var(--sn-bg) 100%
            );
            border: 1px solid rgba(0,0,0,0.08);
            box-shadow:
                0 1px 0 rgba(255,255,255,0.10),
                0 2px 4px rgba(0,0,0,0.08);
            transition: all 150ms ease;
        }
        .search-result-row:hover {
            background: linear-gradient(180deg,
                var(--sn-accent) 0%,
                rgba(0,0,0,0.06) 100%
            );
            border-color: rgba(0,0,0,0.15);
            box-shadow:
                0 1px 0 rgba(255,255,255,0.15),
                0 3px 8px rgba(0,0,0,0.15);
        }
        .search-result-row label {
            color: var(--sn-text);
            text-shadow: 0 1px 0 rgba(255,255,255,0.12);
        }
    """

    def __init__(self, on_launched=None, icon_size=32):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._on_launched = on_launched
        self._all_bundles = []
        self._icon_size = icon_size

        provider = Gtk.CssProvider()
        provider.load_from_string(self._CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.set_valign(Gtk.Align.CENTER)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Type to search...")
        self._search_entry.set_margin_start(48)
        self._search_entry.set_margin_end(48)
        self._search_entry.set_hexpand(True)
        self._search_entry.connect("search-changed", self._on_search_changed)
        self.append(self._search_entry)

        self._results = Gtk.ListBox()
        self._results.set_selection_mode(Gtk.SelectionMode.NONE)
        self._results.set_margin_start(48)
        self._results.set_margin_end(48)
        self._results.set_margin_top(8)
        self._results.set_visible(False)
        self.append(self._results)

    def set_bundles(self, bundles):
        self._all_bundles = list(bundles)

    def _on_search_changed(self, entry):
        while child := self._results.get_first_child():
            self._results.remove(child)
        text = entry.get_text().strip().lower()
        if not text:
            self._results.set_visible(False)
            return
        matches = [b for b in self._all_bundles if text in b.name.lower()]
        for bundle in matches[:10]:
            self._results.append(
                _ResultRow(bundle, self._launch, icon_size=self._icon_size)
            )
        self._results.set_visible(bool(matches))

    def set_icon_size(self, icon_size):
        self._icon_size = icon_size
        self._on_search_changed(self._search_entry)

    def _launch(self, bundle):
        bundle.launch()
        if self._on_launched is not None:
            self._on_launched(bundle)

    def on_activate(self):
        pass

    def on_deactivate(self):
        # Preserve search text and results across view switches
        # (frame-views spec). Nothing is reset.
        pass
