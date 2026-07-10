"""Home View container.

A **view** is a way of seeing your system — Desktop, Apps, Search — that
the learner navigates between from the Frame (not a layout selected in
Settings; see the frame-views spec). Each view is a ``Gtk.Widget`` that
declares a ``view_id`` class attribute and MAY define ``on_activate`` /
``on_deactivate`` methods, called when it becomes visible or is switched
away from. There is no base class or mixin to inherit: a view is anything
with a ``view_id`` — duck typing keeps the contract to one attribute.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class HomeView(Gtk.Stack):
    """Container that swaps between registered views."""

    __gtype_name__ = "SugarNextHomeView"

    def __init__(self):
        super().__init__()
        self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._views = {}
        self._active_id = None

    def add_view(self, view, set_active=False):
        view_id = getattr(view, "view_id", None)
        if view_id is None:
            raise ValueError("a view must declare a view_id")
        self._views[view_id] = view
        self.add_named(view, view_id)
        if set_active or self._active_id is None:
            self.set_active(view_id)

    def set_active(self, view_id):
        if view_id not in self._views:
            raise KeyError(f"unknown view {view_id!r}")
        if view_id == self._active_id:
            return
        previous = self._views.get(self._active_id)
        if previous is not None and hasattr(previous, "on_deactivate"):
            previous.on_deactivate()
        self._active_id = view_id
        self.set_visible_child_name(view_id)
        current = self._views[view_id]
        if hasattr(current, "on_activate"):
            current.on_activate()

    @property
    def active_id(self):
        return self._active_id

    def view_ids(self):
        return list(self._views.keys())

    def get_view(self, view_id):
        return self._views.get(view_id)
