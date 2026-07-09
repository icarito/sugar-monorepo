"""Example extension: log shell events to stdout.

Install by copying into ~/.local/share/sugar-next/extensions/.
"""


def on_shell_start():
    print("[logger] Sugar Next shell started")


def on_app_launch(app_id, app_info):
    print(f"[logger] launching {app_id} ({app_info.get_display_name()})")
