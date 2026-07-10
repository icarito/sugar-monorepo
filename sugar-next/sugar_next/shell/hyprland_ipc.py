"""Hyprland IPC helpers for Sugar Next session integration."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import subprocess

from sugar_next.shell.app_state import normalize_app_id

log = logging.getLogger("sugar-next.hyprland-ipc")


@dataclass(frozen=True)
class HyprlandClient:
    """A mapped Hyprland client relevant to the Frame."""

    app_id: str
    title: str = ""
    address: str = ""
    workspace_id: int | None = None
    mapped: bool = True

    @property
    def normalized_app_id(self) -> str:
        return normalize_app_id(self.app_id)


@dataclass(frozen=True)
class HyprlandState:
    """Current compositor state as read from hyprctl JSON output."""

    clients: tuple[HyprlandClient, ...]
    focused_app_id: str | None
    workspaces: tuple[dict, ...]


class HyprlandIPC:
    """Small wrapper around ``hyprctl -j`` and dispatch commands."""

    POLL_INTERVAL_MS = 500

    def __init__(self, runner=None):
        self._runner = runner or self._run_hyprctl

    @staticmethod
    def is_session() -> bool:
        return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))

    def snapshot(self) -> HyprlandState:
        clients_raw = self._json("clients")
        active_raw = self._json("activewindow")
        workspaces_raw = self._json("workspaces")
        clients = tuple(self._parse_clients(clients_raw))
        focused = normalize_app_id(active_raw.get("class")) or None
        return HyprlandState(
            clients=clients,
            focused_app_id=focused,
            workspaces=tuple(workspaces_raw if isinstance(workspaces_raw, list) else ()),
        )

    def focus_window(self, app_id: str) -> bool:
        norm = normalize_app_id(app_id)
        if not norm:
            return False
        selector = _lua_quote(f"class:^{norm}$")
        result = self._runner(
            ["hyprctl", "dispatch", f"hl.dsp.focus({{ window = {selector} }})"],
            check=False,
        )
        return getattr(result, "returncode", 1) == 0

    def _json(self, command: str):
        result = self._runner(["hyprctl", command, "-j"], check=True)
        text = getattr(result, "stdout", "") or ""
        return json.loads(text or "{}")

    @staticmethod
    def _parse_clients(raw_clients) -> list[HyprlandClient]:
        if not isinstance(raw_clients, list):
            return []
        clients = []
        for raw in raw_clients:
            if not isinstance(raw, dict):
                continue
            app_id = raw.get("class") or raw.get("initialClass") or ""
            if not normalize_app_id(app_id):
                continue
            workspace = raw.get("workspace") or {}
            workspace_id = workspace.get("id") if isinstance(workspace, dict) else None
            mapped = bool(raw.get("mapped", True))
            if not mapped:
                continue
            clients.append(
                HyprlandClient(
                    app_id=app_id,
                    title=raw.get("title") or "",
                    address=raw.get("address") or "",
                    workspace_id=workspace_id,
                    mapped=mapped,
                )
            )
        return clients

    @staticmethod
    def _run_hyprctl(args, check):
        try:
            return subprocess.run(
                args,
                check=check,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except (OSError, subprocess.SubprocessError):
            log.exception("hyprctl command failed: %s", " ".join(args))
            raise


def _lua_quote(value: str) -> str:
    return json.dumps(value)
