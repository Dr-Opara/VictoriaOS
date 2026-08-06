from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CalendarEventData:
    """Normalized calendar event data used across providers."""

    id: int | None
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime

    def to_prompt_dict(self) -> dict[str, str]:
        """Return a compact representation safe to pass into an AI prompt."""
        return {
            "title": self.title,
            "start": self.start_time.isoformat(),
            "end": self.end_time.isoformat(),
            "location": self.location,
        }


class CalendarConfigurationError(RuntimeError):
    """Raised when a calendar provider's settings are missing or invalid."""


class CalendarProviderError(RuntimeError):
    """Raised when a calendar provider cannot complete a requested operation."""


class CalendarEventNotFoundError(RuntimeError):
    """Raised when an operation targets an event that doesn't exist."""
