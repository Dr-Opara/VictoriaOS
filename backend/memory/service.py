from __future__ import annotations

from datetime import datetime, timezone

from backend.database.models import Memory
from backend.memory.models import MemoryItem
from backend.memory.store import MemoryStore


class MemoryService:
    """Victoria's long-term memory: durable facts that persist across restarts."""

    def __init__(self, store: MemoryStore | None = None) -> None:
        self.store = store or MemoryStore()

    def remember(self, key: str, value: str) -> Memory:
        """Persist a new fact under ``key``."""
        item = MemoryItem(key=key.strip(), value=value.strip(), created_at=datetime.now(timezone.utc))
        return self.store.save(item)

    def recall(self, key: str) -> list[Memory]:
        """Return every memory stored under ``key``, most recent first."""
        return self.store.get(key)

    def recent(self, limit: int = 20) -> list[Memory]:
        """Return the most recently remembered facts."""
        return self.store.recent(limit=limit)

    def search(self, query: str, limit: int = 20) -> list[Memory]:
        """Return memories whose key or value contains ``query``."""
        return self.store.search(query, limit=limit)

    def forget(self, key: str) -> int:
        """Delete every memory stored under ``key``. Returns the count removed."""
        return self.store.delete(key)

    def clear(self) -> int:
        """Delete all memories. Returns the count removed."""
        return self.store.clear()

    def memories(self) -> list[Memory]:
        """Return every remembered fact, most recent first."""
        return self.store.all()
