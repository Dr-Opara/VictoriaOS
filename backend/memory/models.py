from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class MemoryItem:
    """A lightweight, storage-agnostic view of a remembered fact."""

    key: str
    value: str
    created_at: datetime
