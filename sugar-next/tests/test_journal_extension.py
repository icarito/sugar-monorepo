import sqlite3
import types
from pathlib import Path

from sugar_next.api.hooks import HookRegistry

EXAMPLES = Path(__file__).parent.parent / "examples" / "extensions"


def test_journal_records_launch(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    extensions = tmp_path / "sugar-next" / "extensions"
    extensions.mkdir(parents=True)
    (extensions / "journal.py").write_text(
        (EXAMPLES / "journal.py").read_text()
    )

    registry = HookRegistry()
    registry.load(extensions)
    app_info = types.SimpleNamespace(get_display_name=lambda: "Fake App")
    registry.call("on_app_launch", "fake.desktop", app_info)

    db = tmp_path / "sugar-next" / "journal.sqlite"
    rows = sqlite3.connect(db).execute(
        "SELECT app_id, title, kind FROM entries"
    ).fetchall()
    assert rows == [("fake.desktop", "Fake App", "launch")]
