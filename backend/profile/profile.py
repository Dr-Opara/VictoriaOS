from __future__ import annotations

import re

from sqlalchemy import select

from backend.database.database import session_scope
from backend.database.models import UserPreference

_REMEMBER_PREFERENCE_PATTERN = re.compile(
    r"remember\s+(?:that\s+)?my\s+(?P<key>.+?)\s+is\s+(?P<value>.+)",
    re.IGNORECASE,
)


class UserProfile:
    """Permanent user preferences, e.g. favorite airline or hotel chain."""

    def set_preference(self, key: str, value: str) -> UserPreference:
        """Create or update a preference by key."""
        normalized_key = key.strip().lower()
        db = session_scope()
        try:
            existing = db.scalar(
                select(UserPreference).where(UserPreference.key == normalized_key)
            )
            if existing:
                existing.value = value.strip()
                db.commit()
                db.refresh(existing)
                return existing

            record = UserPreference(key=normalized_key, value=value.strip())
            db.add(record)
            db.commit()
            db.refresh(record)
            return record
        finally:
            db.close()

    def get_preference(self, key: str) -> str | None:
        """Return a preference value by key, or ``None`` if unset."""
        db = session_scope()
        try:
            record = db.scalar(
                select(UserPreference).where(UserPreference.key == key.strip().lower())
            )
            return record.value if record else None
        finally:
            db.close()

    def all_preferences(self) -> list[UserPreference]:
        """Return every stored preference."""
        db = session_scope()
        try:
            return list(db.scalars(select(UserPreference).order_by(UserPreference.key)))
        finally:
            db.close()

    @staticmethod
    def parse_preference_command(command: str) -> tuple[str, str] | None:
        """Extract a ``(key, value)`` pair from a 'remember my X is Y' command."""
        match = _REMEMBER_PREFERENCE_PATTERN.search(command.strip())
        if not match:
            return None

        return match.group("key").strip(), match.group("value").strip().rstrip(".")
