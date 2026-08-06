from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.integrations.calendar.models import CalendarEventData, CalendarEventNotFoundError
from backend.integrations.calendar.service import CalendarService
from backend.security.audit import audit_log

router = APIRouter(prefix="/calendar", tags=["Calendar"])
calendar_service = CalendarService()


class CreateEventRequest(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    description: str = ""
    location: str = ""


class RescheduleEventRequest(BaseModel):
    start_time: datetime
    end_time: datetime


def _serialize(event: CalendarEventData) -> dict:
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "location": event.location,
        "start_time": event.start_time,
        "end_time": event.end_time,
    }


@router.get("/today")
def today():
    """Return today's schedule, earliest first."""
    return {"events": [_serialize(event) for event in calendar_service.today_schedule()]}


@router.get("/upcoming")
def upcoming(limit: int = 10):
    """Return upcoming events."""
    return {"events": [_serialize(event) for event in calendar_service.upcoming(limit=limit)]}


@router.post("/events")
def create_event(request: CreateEventRequest):
    """Schedule a new meeting."""
    event = calendar_service.create_meeting(
        request.title, request.start_time, request.end_time, request.description, request.location
    )
    audit_log("calendar.create", f"id={event.id} title={event.title!r}")
    return _serialize(event)


@router.patch("/events/{event_id}")
def reschedule_event(event_id: int, request: RescheduleEventRequest):
    """Reschedule an existing event."""
    try:
        event = calendar_service.reschedule(event_id, request.start_time, request.end_time)
    except CalendarEventNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    audit_log("calendar.reschedule", f"id={event_id}")
    return _serialize(event)


@router.delete("/events/{event_id}")
def cancel_event(event_id: int):
    """Cancel an event."""
    if not calendar_service.cancel(event_id):
        raise HTTPException(status_code=404, detail="Event not found.")

    audit_log("calendar.cancel", f"id={event_id}")
    return {"status": "cancelled", "id": event_id}
