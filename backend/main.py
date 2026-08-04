from fastapi import FastAPI

from backend.config.settings import get_settings
from backend.core.logger import logger
from backend.core.assistant import VictoriaAssistant
from backend.voice.engine import VoiceEngine
from backend.api.assistant import router as assistant_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Private AI Executive Assistant",
    version=settings.app_version,
)

logger.info("VictoriaOS started successfully.")

voice = VoiceEngine()
assistant = VictoriaAssistant()
app.include_router(assistant_router)

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
async def think(command: str):
    return assistant.think(command)