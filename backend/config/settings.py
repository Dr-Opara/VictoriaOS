from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "VictoriaOS"
    app_version: str = "1.0.0"
    environment: str = "development"

    openai_api_key: str = ""

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