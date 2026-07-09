"""Example extension: count how many times each app is launched.

Counts are persisted as JSON in ~/.local/share/sugar-next/launch-counts.json.
Install by copying into ~/.local/share/sugar-next/extensions/.
"""

import json
import os
from pathlib import Path

_data_home = os.environ.get(
    "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
)
_counts_file = Path(_data_home) / "sugar-next" / "launch-counts.json"


def on_app_launch(app_id, app_info):
    counts = {}
    if _counts_file.is_file():
        try:
            counts = json.loads(_counts_file.read_text())
        except ValueError:
            counts = {}
    counts[app_id] = counts.get(app_id, 0) + 1
    _counts_file.parent.mkdir(parents=True, exist_ok=True)
    _counts_file.write_text(json.dumps(counts, indent=2))
    print(f"[launch-counter] {app_id} launched {counts[app_id]} time(s)")
