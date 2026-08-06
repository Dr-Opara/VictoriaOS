from functools import lru_cache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "VictoriaOS"
    app_version: str = "1.0.0"
    environment: str = "development"

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("MODEL", "gpt-5")

    database_url: str = ""
    redis_url: str = ""

    log_level: str = "INFO"

    dashboard_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    api_key: str = os.getenv("API_KEY", "")
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    google_calendar_client_id: str = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
    google_calendar_client_secret: str = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")

    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    weather_location: str = os.getenv("WEATHER_LOCATION", "")

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()