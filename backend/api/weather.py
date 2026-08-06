from __future__ import annotations

from fastapi import APIRouter

from backend.integrations.weather.models import WeatherConfigurationError, WeatherProviderError
from backend.integrations.weather.service import WeatherService

router = APIRouter(prefix="/weather", tags=["Weather"])
weather_service = WeatherService()


@router.get("/current")
def current_weather():
    """Return current conditions, or a configuration status if unset."""
    if not weather_service.is_configured:
        return {"configured": False}

    try:
        report = weather_service.current()
    except (WeatherConfigurationError, WeatherProviderError) as error:
        return {"configured": True, "error": str(error)}

    return {"configured": True, **report.to_prompt_dict()}
