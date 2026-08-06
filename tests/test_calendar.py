from datetime import datetime, timedelta, timezone

from backend.integrations.calendar.models import CalendarEventNotFoundError
from backend.integrations.calendar.service import CalendarService


def test_create_and_list_today():
    service = CalendarService()
    now = datetime.now(timezone.utc)

    event = service.create_meeting("Board meeting", now + timedelta(hours=1), now + timedelta(hours=2))
    assert event.id is not None

    todays = service.today_schedule(now=now)
    assert any(e.id == event.id for e in todays)


def test_upcoming_excludes_past_events():
    service = CalendarService()
    now = datetime.now(timezone.utc)

    past_event = service.create_meeting("Past", now - timedelta(days=1), now - timedelta(days=1) + timedelta(hours=1))
    future_event = service.create_meeting("Future", now + timedelta(days=1), now + timedelta(days=1, hours=1))

    upcoming_ids = {e.id for e in service.upcoming(limit=50, now=now)}
    assert future_event.id in upcoming_ids
    assert past_event.id not in upcoming_ids


def test_reschedule_updates_times():
    service = CalendarService()
    now = datetime.now(timezone.utc)
    event = service.create_meeting("Standup", now, now + timedelta(minutes=30))

    new_start = now + timedelta(days=1)
    new_end = new_start + timedelta(minutes=30)
    updated = service.reschedule(event.id, new_start, new_end)

    # SQLite drops tzinfo on round-trip; compare naive-UTC equivalents.
    assert updated.start_time.replace(tzinfo=timezone.utc) == new_start
    assert updated.end_time.replace(tzinfo=timezone.utc) == new_end


def test_reschedule_missing_event_raises():
    service = CalendarService()
    now = datetime.now(timezone.utc)

    try:
        service.reschedule(999999, now, now + timedelta(hours=1))
        assert False, "expected CalendarEventNotFoundError"
    except CalendarEventNotFoundError:
        pass


def test_cancel_removes_event():
    service = CalendarService()
    now = datetime.now(timezone.utc)
    event = service.create_meeting("Temp", now, now + timedelta(hours=1))

    assert service.cancel(event.id) is True
    assert service.cancel(event.id) is False
