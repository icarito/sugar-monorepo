import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pytest

from sugar_next.shell.app_grid import SugarAppGrid


@pytest.fixture(autouse=True)
def gtk_display():
    if not Gtk.init_check():
        pytest.skip("no display available for GTK")


def test_filter_unwraps_flowboxchild():
    # Regression: FlowBox passes Gtk.FlowBoxChild wrappers to the filter
    # func; matching against the wrapper itself filtered everything out.
    grid = SugarAppGrid()
    child = grid._flow_box.get_first_child()
    assert isinstance(child, Gtk.FlowBoxChild)

    grid._search_entry.set_text("")
    assert grid._filter_func(child) is True

    name = child.get_child().bundle.name
    grid._search_entry.set_text(name[:4].lower())
    assert grid._filter_func(child) is True

    grid._search_entry.set_text("definitely-no-such-app-xyz")
    assert grid._filter_func(child) is False
