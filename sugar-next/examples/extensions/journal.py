"""Journal extension: record app launches into a local SQLite journal.

Opt-in by design — the Journal only exists if you install this extension:

    cp journal.py ~/.local/share/sugar-next/extensions/

Entries land in ~/.local/share/sugar-next/journal.sqlite. Inspect with:

    sqlite3 ~/.local/share/sugar-next/journal.sqlite \
        'SELECT timestamp, app_id, kind FROM entries ORDER BY id DESC LIMIT 10'
"""

import datetime
import os
import sqlite3
from pathlib import Path

_data_home = os.environ.get(
    "XDG_DATA_HOME", os.path.expanduser("~/.local/share")
)
_db_path = Path(_data_home) / "sugar-next" / "journal.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    app_id TEXT NOT NULL,
    title TEXT NOT NULL,
    kind TEXT NOT NULL
)
"""


def _connect():
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(_db_path)
    connection.execute(_SCHEMA)
    return connection


def _record(app_id, title, kind):
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    with _connect() as connection:
        connection.execute(
            "INSERT INTO entries (timestamp, app_id, title, kind)"
            " VALUES (?, ?, ?, ?)",
            (timestamp, app_id, title, kind),
        )


def on_app_launch(app_id, app_info):
    _record(app_id, app_info.get_display_name(), "launch")
