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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings():
    return Settings()