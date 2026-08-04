from __future__ import annotations

from backend.core.logger import logger
from backend.database import models  # noqa: F401  (ensures models are registered on Base)
from backend.database.base import Base
from backend.database.database import engine


def run_migrations() -> None:
    """Create any tables that do not yet exist.

    VictoriaOS uses SQLite for now, so a full Alembic migration chain is not
    required. This creates missing tables idempotently on every startup.
    """
    logger.info("Running database migrations (create_all).")
    Base.metadata.create_all(bind=engine)
