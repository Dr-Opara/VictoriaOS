from __future__ import annotations

from datetime import datetime

from backend.config.settings import get_settings
from backend.integrations.calendar.models import (
    CalendarConfigurationError,
    CalendarEventData,
)


class GoogleCalendarProvider:
    """Google Calendar provider - requires a configured OAuth app.

    Not implemented against the live Google Calendar API: doing so needs a
    registered Google Cloud OAuth client (client id/secret), a consent
    screen, and a real user authorization flow, none of which exist in this
    environment. Every method raises ``CalendarConfigurationError`` until
    ``GOOGLE_CALENDAR_CLIENT_ID``/``GOOGLE_CALENDAR_CLIENT_SECRET`` are set,
    so callers get a clear, honest error instead of a silent no-op or fake
    data. See docs/ROADMAP.md.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._configured = bool(
            settings.google_calendar_client_id and settings.google_calendar_client_secret
        )

    def _require_configured(self) -> None:
        if not self._configured:
            raise CalendarConfigurationError(
                "Google Calendar is not configured. Set GOOGLE_CALENDAR_CLIENT_ID and "
                "GOOGLE_CALENDAR_CLIENT_SECRET, and complete the OAuth consent flow, "
                "before using this provider."
            )

    def today(self, now: datetime | None = None) -> list[CalendarEventData]:
        self._require_configured()
        raise NotImplementedError  # pragma: no cover - unreachable without real OAuth

    def upcoming(self, limit: int = 10, now: datetime | None = None) -> list[CalendarEventData]:
        self._require_configured()
        raise NotImplementedError  # pragma: no cover - unreachable without real OAuth
