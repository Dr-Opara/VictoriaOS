from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config.settings import get_settings
from backend.core.logger import logger
from backend.database.base import Base
from backend.database import models  # noqa: F401  (ensures models are registered on Base)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_SQLITE_URL = f"sqlite:///{(DATA_DIR / 'victoria.db').as_posix()}"


def _resolve_database_url() -> str:
    """Return the configured database URL, defaulting to a local SQLite file."""
    settings = get_settings()
    return settings.database_url or DEFAULT_SQLITE_URL


DATABASE_URL = _resolve_database_url()

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for use as a FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_scope() -> Session:
    """Return a new database session for manual use outside of FastAPI."""
    return SessionLocal()


def init_database() -> None:
    """Create any tables that do not yet exist (idempotent)."""
    logger.info("Initializing database schema.")
    Base.metadata.create_all(bind=engine)
