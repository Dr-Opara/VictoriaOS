import sqlite3
import time
from pathlib import Path

from scripts.backup_db import backup_database, prune_old_backups


def _make_sqlite_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()


def test_backup_database_copies_file(tmp_path):
    db_path = tmp_path / "victoria.db"
    backup_dir = tmp_path / "backups"
    _make_sqlite_db(db_path)

    destination = backup_database(db_path=db_path, backup_dir=backup_dir)

    assert destination.exists()
    assert sqlite3.connect(destination).execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchone() == ("t",)


def test_backup_database_missing_source_raises(tmp_path):
    try:
        backup_database(db_path=tmp_path / "missing.db", backup_dir=tmp_path / "backups")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_prune_old_backups_keeps_only_the_newest(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    for index in range(5):
        (backup_dir / f"victoria-{index}.db").write_text("data")
        time.sleep(0.01)

    removed = prune_old_backups(backup_dir, keep=2)

    remaining = sorted(backup_dir.glob("victoria-*.db"))
    assert len(remaining) == 2
    assert len(removed) == 3
