"""Back up the VictoriaOS SQLite database.

Usage: ``python scripts/backup_db.py [--keep N]``

Copies ``data/victoria.db`` to ``backups/victoria-<timestamp>.db`` using
SQLite's online backup API (safe to run while the app is live), then prunes
old backups beyond ``--keep`` (default 14).
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data") / "victoria.db"
BACKUP_DIR = Path("backups")


def backup_database(db_path: Path = DB_PATH, backup_dir: Path = BACKUP_DIR) -> Path:
    """Create a timestamped backup of the SQLite database and return its path."""
    if not db_path.exists():
        raise FileNotFoundError(f"No database found at {db_path}")

    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"victoria-{timestamp}.db"

    source_conn = sqlite3.connect(db_path)
    dest_conn = sqlite3.connect(destination)
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()

    return destination


def prune_old_backups(backup_dir: Path, keep: int) -> list[Path]:
    """Delete all but the ``keep`` most recent backups. Returns deleted paths."""
    backups = sorted(backup_dir.glob("victoria-*.db"), reverse=True)
    stale = backups[keep:]
    for backup in stale:
        backup.unlink()

    return stale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", type=int, default=14, help="Number of backups to retain.")
    args = parser.parse_args()

    try:
        destination = backup_database()
    except FileNotFoundError as error:
        print(f"Skipping backup: {error}", file=sys.stderr)
        sys.exit(0)

    print(f"Backed up database to {destination}")

    removed = prune_old_backups(BACKUP_DIR, args.keep)
    if removed:
        print(f"Pruned {len(removed)} old backup(s).")


if __name__ == "__main__":
    main()
