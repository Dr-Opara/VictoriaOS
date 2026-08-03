from fastapi import FastAPI

from backend.config.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Private AI Executive Assistant",
    version=settings.app_version,
)


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