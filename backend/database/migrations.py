from __future__ import annotations

from backend.database.database import init_database


def run_migrations() -> None:
    """Create any tables that do not yet exist.

    VictoriaOS uses SQLite for now, so a full Alembic migration chain is not
    required. This creates missing tables idempotently on every startup.
    """
    init_database()
