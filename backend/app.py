from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.assistant import router as assistant_router
from backend.api.briefing import router as briefing_router
from backend.api.calendar import router as calendar_router
from backend.api.knowledge import router as knowledge_router
from backend.api.memory import router as memory_router
from backend.api.system import router as system_router
from backend.api.task import router as task_router
from backend.api.voice import router as voice_router
from backend.api.weather import router as weather_router
from backend.config.settings import get_settings
from backend.core.assistant import VictoriaAssistant
from backend.core.logger import logger
from backend.database.migrations import run_migrations
from backend.security.api_key import ApiKeyMiddleware
from backend.security.headers import SecurityHeadersMiddleware
from backend.security.rate_limit import RateLimitMiddleware
from backend.voice.engine import VoiceEngine

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Private AI Executive Assistant",
    version=settings.app_version,
)

run_migrations()

logger.info("VictoriaOS started successfully.")

# Middleware executes in reverse of registration order (last added runs
# first on the request). Registered here so the effective request order is:
# security headers -> rate limit -> API key -> CORS -> request logging -> route.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.add_middleware(ApiKeyMiddleware, api_key=settings.api_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.dashboard_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

voice = VoiceEngine()
assistant = VictoriaAssistant()

app.include_router(assistant_router)
app.include_router(memory_router)
app.include_router(task_router)
app.include_router(voice_router)
app.include_router(system_router)
app.include_router(calendar_router)
app.include_router(weather_router)
app.include_router(briefing_router)
app.include_router(knowledge_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with timing and any error that occurred."""
    start_time = time.monotonic()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.monotonic() - start_time) * 1000
        logger.exception(
            "Request failed | method=%s path=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.monotonic() - start_time) * 1000
    logger.info(
        "Request handled | method=%s path=%s status=%s duration_ms=%.1f model=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        settings.model,
    )
    return response


@app.get("/")
async def root():
    return {
        "assistant": "Victoria",
        "status": "Online",
        "owner": "Dr. Opara",
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/voice")
async def voice_test(text: str):
    return voice.process(text)


@app.get("/think")
async def think(command: str, session_id: str = "default"):
    return assistant.think(command, session_id=session_id)
