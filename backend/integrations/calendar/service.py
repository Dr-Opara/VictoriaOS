from __future__ import annotations

from datetime import datetime

from backend.integrations.calendar.local import LocalCalendarProvider
from backend.integrations.calendar.models import CalendarEventData


class CalendarService:
    """High-level calendar workflows for Victoria's executive assistant.

    Always backed by the local calendar provider - the only one that works
    without external OAuth credentials. Google/Microsoft calendars are
    designed as pluggable providers (see ``manager.py``/``google.py``) that
    this service can be pointed at once real credentials exist, without
    changing any call site.
    """

    def __init__(self, provider: LocalCalendarProvider | None = None) -> None:
        self.provider = provider or LocalCalendarProvider()

    def today_schedule(self, now: datetime | None = None) -> list[CalendarEventData]:
        """Return today's events, earliest first."""
        return self.provider.today(now=now)

    def upcoming(self, limit: int = 10, now: datetime | None = None) -> list[CalendarEventData]:
        """Return the next ``limit`` upcoming events."""
        return self.provider.upcoming(limit=limit, now=now)

    def create_meeting(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
    ) -> CalendarEventData:
        """Schedule a new meeting."""
        return self.provider.create_event(title, start_time, end_time, description, location)

    def reschedule(
        self, event_id: int, start_time: datetime, end_time: datetime
    ) -> CalendarEventData:
        """Move an existing event to a new time."""
        return self.provider.update_event(event_id, start_time=start_time, end_time=end_time)

    def cancel(self, event_id: int) -> bool:
        """Cancel (delete) an event. Returns ``True`` if it existed."""
        return self.provider.cancel_event(event_id)
