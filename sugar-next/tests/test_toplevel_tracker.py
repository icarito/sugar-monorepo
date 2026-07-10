"""Tests for the wlr-foreign-toplevel-management client.

This dev environment runs GNOME/Mutter, which implements neither
zwlr_foreign_toplevel_manager_v1 nor the newer ext_foreign_toplevel_list_v1
standard (confirmed via `wayland-info` — deliberate GNOME design choice,
not a missing feature). So the only behavior verifiable here is protocol
non-availability handling plus a source-level guard on the event loop;
the actual toplevel create/close/focus event flow needs a real wlroots
compositor (Wayfire/Hyprland) to exercise — see dev/run-wayfire.sh.
"""

import inspect
import time

import pytest

from sugar_next.shell.toplevel_tracker import TopLevelTracker, _HAS_PYWAYLAND


@pytest.fixture(autouse=True)
def wayland_display():
    import os

    if not os.environ.get("WAYLAND_DISPLAY"):
        pytest.skip("no Wayland display available")


def test_available_is_none_before_start():
    tracker = TopLevelTracker()
    assert tracker.available is None


@pytest.mark.skipif(not _HAS_PYWAYLAND, reason="pywayland not installed")
def test_start_and_stop_do_not_raise():
    tracker = TopLevelTracker()
    tracker.start()
    time.sleep(1.0)
    # available is False here specifically because this dev environment
    # is GNOME/Mutter, which does not offer the protocol at all — not
    # because of a bug. On a real Wayfire session this would be True.
    assert tracker.available is False
    tracker.stop()
    time.sleep(0.3)
    assert tracker._thread.is_alive() is False


def test_reports_unavailable_without_pywayland(monkeypatch):
    monkeypatch.setattr(
        "sugar_next.shell.toplevel_tracker._HAS_PYWAYLAND", False
    )
    tracker = TopLevelTracker()
    tracker.start()
    assert tracker.available is False


def test_event_loop_uses_flushing_roundtrip_not_bare_dispatch():
    # Regression guard: dispatch(block=True) does NOT flush the manager
    # bind, so the compositor never streams toplevels and no event is
    # delivered — the tracker looked "available" but did nothing. The loop
    # must use roundtrip() (which flushes) instead. A behavioural test
    # would need a live wlroots compositor the CI environment lacks, so we
    # assert the loop mechanism by source inspection to stop a refactor
    # from silently reintroducing the broken form.
    # Strip comments so the guard checks the actual code, not the
    # explanatory comment that (deliberately) names the broken form.
    code = "\n".join(
        line.split("#", 1)[0]
        for line in inspect.getsource(TopLevelTracker._run).splitlines()
    )
    assert "roundtrip()" in code, "event loop must roundtrip (flushes requests)"
    assert "dispatch(block=True)" not in code, (
        "dispatch(block=True) does not flush the bind; no events are "
        "delivered — use roundtrip() in the loop"
    )
