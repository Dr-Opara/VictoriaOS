from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.database import session_scope
from backend.database.models import Memory
from backend.memory.models import MemoryItem


class MemoryStore:
    """SQLite-backed persistence for Victoria's long-term memory."""

    def __init__(self, db: Session | None = None) -> None:
        self._db = db

    def _session(self) -> Session:
        return self._db or session_scope()

    def save(self, item: MemoryItem) -> Memory:
        db = self._session()
        try:
            record = Memory(key=item.key, value=item.value, created_at=item.created_at)
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            if self._db is None:
                db.close()

    def get(self, key: str) -> list[Memory]:
        db = self._session()
        try:
            statement = (
                select(Memory).where(Memory.key == key).order_by(Memory.created_at.desc())
            )
            return list(db.scalars(statement))
        finally:
            if self._db is None:
                db.close()

    def recent(self, limit: int = 20) -> list[Memory]:
        db = self._session()
        try:
            statement = select(Memory).order_by(Memory.created_at.desc()).limit(limit)
            return list(db.scalars(statement))
        finally:
            if self._db is None:
                db.close()

    def search(self, query: str, limit: int = 20) -> list[Memory]:
        db = self._session()
        try:
            like_query = f"%{query}%"
            statement = (
                select(Memory)
                .where((Memory.key.ilike(like_query)) | (Memory.value.ilike(like_query)))
                .order_by(Memory.created_at.desc())
                .limit(limit)
            )
            return list(db.scalars(statement))
        finally:
            if self._db is None:
                db.close()

    def delete(self, key: str) -> int:
        db = self._session()
        try:
            statement = select(Memory).where(Memory.key == key)
            records = list(db.scalars(statement))
            for record in records:
                db.delete(record)
            db.commit()
            return len(records)
        finally:
            if self._db is None:
                db.close()

    def clear(self) -> int:
        db = self._session()
        try:
            records = list(db.scalars(select(Memory)))
            for record in records:
                db.delete(record)
            db.commit()
            return len(records)
        finally:
            if self._db is None:
                db.close()

    def all(self) -> list[Memory]:
        db = self._session()
        try:
            return list(db.scalars(select(Memory).order_by(Memory.created_at.desc())))
        finally:
            if self._db is None:
                db.close()
