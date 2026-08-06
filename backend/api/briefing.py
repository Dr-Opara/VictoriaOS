from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from backend.core.briefing import DailyBriefingService

router = APIRouter(prefix="/briefing", tags=["Briefing"])
briefing_service = DailyBriefingService()


@router.get("")
async def get_briefing():
    """Generate Victoria's executive daily briefing as text."""
    text = await run_in_threadpool(briefing_service.generate)
    return {"briefing": text}


@router.get("/voice")
async def get_briefing_voice():
    """Generate the daily briefing and return it as spoken audio (MP3)."""
    text = await run_in_threadpool(briefing_service.generate)
    audio = await run_in_threadpool(briefing_service.generate_audio, text)
    return Response(content=audio, media_type="audio/mpeg")
