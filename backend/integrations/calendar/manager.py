from __future__ import annotations

import logging

from backend.integrations.calendar.google import GoogleCalendarProvider
from backend.integrations.calendar.local import LocalCalendarProvider

logger = logging.getLogger("VictoriaOS")


class CalendarManager:
    """Registry and factory for configured calendar providers."""

    def __init__(self) -> None:
        self._providers: dict[str, object] = {}
        self.register("local", LocalCalendarProvider())
        self.register("google", GoogleCalendarProvider())

    def register(self, name: str, provider: object) -> None:
        """Register a calendar provider instance by name."""
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise ValueError("Calendar provider name cannot be empty.")

        self._providers[normalized_name] = provider
        logger.info("Registered calendar provider %s.", normalized_name)

    def provider(self, name: str) -> object | None:
        """Return a registered provider by name."""
        return self._providers.get(name.strip().lower())

    def providers_list(self) -> list[str]:
        """Return the registered calendar provider names."""
        return sorted(self._providers)
