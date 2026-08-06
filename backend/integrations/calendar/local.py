from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from backend.database.database import session_scope
from backend.database.models import CalendarEvent
from backend.integrations.calendar.models import (
    CalendarEventData,
    CalendarEventNotFoundError,
)


class LocalCalendarProvider:
    """A first-party calendar stored in VictoriaOS's own SQLite database.

    This is the default, always-available provider: it needs no external
    OAuth credentials. It does not sync with Google/Microsoft/Yahoo - see
    ``google.py`` for that pluggable (currently unconfigured) provider.
    """

    def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        location: str = "",
    ) -> CalendarEventData:
        db = session_scope()
        try:
            event = CalendarEvent(
                title=title,
                description=description,
                location=location,
                start_time=start_time,
                end_time=end_time,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return self._to_data(event)
        finally:
            db.close()

    def update_event(
        self,
        event_id: int,
        title: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        description: str | None = None,
        location: str | None = None,
    ) -> CalendarEventData:
        db = session_scope()
        try:
            event = db.get(CalendarEvent, event_id)
            if event is None:
                raise CalendarEventNotFoundError(f"No calendar event with id {event_id}.")

            if title is not None:
                event.title = title
            if start_time is not None:
                event.start_time = start_time
            if end_time is not None:
                event.end_time = end_time
            if description is not None:
                event.description = description
            if location is not None:
                event.location = location

            db.commit()
            db.refresh(event)
            return self._to_data(event)
        finally:
            db.close()

    def cancel_event(self, event_id: int) -> bool:
        db = session_scope()
        try:
            event = db.get(CalendarEvent, event_id)
            if event is None:
                return False

            db.delete(event)
            db.commit()
            return True
        finally:
            db.close()

    def list_range(self, start: datetime, end: datetime) -> list[CalendarEventData]:
        db = session_scope()
        try:
            statement = (
                select(CalendarEvent)
                .where(CalendarEvent.start_time >= start)
                .where(CalendarEvent.start_time < end)
                .order_by(CalendarEvent.start_time.asc())
            )
            return [self._to_data(event) for event in db.scalars(statement)]
        finally:
            db.close()

    def today(self, now: datetime | None = None) -> list[CalendarEventData]:
        reference = now or datetime.now(timezone.utc)
        start_of_day = reference.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.list_range(start_of_day, start_of_day + timedelta(days=1))

    def upcoming(self, limit: int = 10, now: datetime | None = None) -> list[CalendarEventData]:
        reference = now or datetime.now(timezone.utc)
        db = session_scope()
        try:
            statement = (
                select(CalendarEvent)
                .where(CalendarEvent.start_time >= reference)
                .order_by(CalendarEvent.start_time.asc())
                .limit(limit)
            )
            return [self._to_data(event) for event in db.scalars(statement)]
        finally:
            db.close()

    @staticmethod
    def _to_data(event: CalendarEvent) -> CalendarEventData:
        return CalendarEventData(
            id=event.id,
            title=event.title,
            description=event.description,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
        )
