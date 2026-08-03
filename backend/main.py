from fastapi import FastAPI

from backend.config.settings import get_settings

from backend.core.logger import logger

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Private AI Executive Assistant",
    version=settings.app_version,
)
logger.info("VictoriaOS started successfully.")

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
from backend.core.assistant import VictoriaAssistant

assistant = VictoriaAssistant()

@app.get("/think")
async def think(command: str):

    return assistant.think(command)