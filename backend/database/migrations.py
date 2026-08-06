from __future__ import annotations

from sqlalchemy import inspect, text

from backend.core.logger import logger
from backend.database.database import engine, init_database

# (table, column, DDL type) for columns added after a table's first release.
# SQLite's ``CREATE TABLE IF NOT EXISTS`` (via ``create_all``) never adds
# columns to an existing table, so additive changes need an explicit,
# idempotent ``ALTER TABLE`` here instead of a full Alembic migration chain.
_ADDITIVE_COLUMNS: list[tuple[str, str, str]] = [
    ("tasks", "priority", "VARCHAR(16)"),
]


def _apply_additive_columns() -> None:
    """Add any columns from ``_ADDITIVE_COLUMNS`` that don't exist yet."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table, column, ddl_type in _ADDITIVE_COLUMNS:
            if table not in existing_tables:
                continue  # create_all will create it with the column already present

            existing_columns = {col["name"] for col in inspector.get_columns(table)}
            if column in existing_columns:
                continue

            logger.info("Migrating: adding column %s.%s", table, column)
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))


def run_migrations() -> None:
    """Create any tables that do not yet exist, and apply additive column changes.

    VictoriaOS uses SQLite for now, so a full Alembic migration chain is not
    required. This creates missing tables idempotently on every startup and
    patches in any new columns on tables that already existed.
    """
    init_database()
    _apply_additive_columns()
