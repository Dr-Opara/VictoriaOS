from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from backend.config.settings import get_settings
from backend.database.database import session_scope
from backend.database.models import ConversationHistory, Memory, Task
from backend.integrations.email.service import EmailService
from backend.integrations.email.models import EmailConfigurationError, EmailProviderError

router = APIRouter(tags=["System"])

_START_TIME = time.monotonic()
LOG_FILE = Path("logs") / "victoria.log"


@router.get("/system/status")
def system_status():
    """Return runtime status: uptime, version, environment, model."""
    settings = get_settings()
    return {
        "status": "online",
        "uptime_seconds": round(time.monotonic() - _START_TIME, 1),
        "version": settings.app_version,
        "environment": settings.environment,
        "model": settings.model,
    }


@router.get("/system/usage")
def system_usage():
    """Return basic AI/executive-assistant usage statistics."""
    db = session_scope()
    try:
        conversation_count = db.scalar(select(func.count()).select_from(ConversationHistory)) or 0
        memory_count = db.scalar(select(func.count()).select_from(Memory)) or 0
        task_count = db.scalar(select(func.count()).select_from(Task)) or 0
        pending_tasks = db.scalar(
            select(func.count()).select_from(Task).where(Task.status == "pending")
        ) or 0

        return {
            "conversation_turns": conversation_count,
            "memories_stored": memory_count,
            "tasks_total": task_count,
            "tasks_pending": pending_tasks,
        }
    finally:
        db.close()


@router.get("/system/logs")
def system_logs(limit: int = Query(default=200, ge=1, le=2000)):
    """Return the most recent lines from the application log."""
    if not LOG_FILE.exists():
        return {"lines": []}

    with LOG_FILE.open("r", encoding="utf-8", errors="replace") as log_file:
        lines = log_file.readlines()

    return {"lines": [line.rstrip("\n") for line in lines[-limit:]]}


@router.get("/email/unread")
def email_unread(limit: int = Query(default=10, ge=1, le=50)):
    """Return unread Yahoo Mail messages, or a configuration status."""
    service = EmailService()
    try:
        messages = service.read_unread(limit=limit)
    except EmailConfigurationError:
        return {"configured": False, "messages": []}
    except EmailProviderError:
        return {"configured": True, "error": "Unable to read Yahoo Mail right now.", "messages": []}

    return {
        "configured": True,
        "messages": [message.to_prompt_dict() for message in messages],
    }
