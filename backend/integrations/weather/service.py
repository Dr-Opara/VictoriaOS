from __future__ import annotations

import logging

import requests

from backend.config.settings import get_settings
from backend.integrations.weather.models import (
    WeatherConfigurationError,
    WeatherProviderError,
    WeatherReport,
)

logger = logging.getLogger("VictoriaOS")

_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherService:
    """Current-conditions weather via OpenWeatherMap.

    Gated behind ``WEATHER_API_KEY``/``WEATHER_LOCATION`` exactly like the
    other optional integrations in this codebase (Yahoo Mail, wake word,
    speaker verification): without a configured key, ``is_configured`` is
    ``False`` and ``current()`` raises a clear ``WeatherConfigurationError``
    rather than returning fabricated conditions.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def is_configured(self) -> bool:
        return bool(self.settings.weather_api_key and self.settings.weather_location)

    def current(self) -> WeatherReport:
        """Fetch current weather for the configured location."""
        if not self.is_configured:
            raise WeatherConfigurationError(
                "Weather is not configured. Set WEATHER_API_KEY and WEATHER_LOCATION."
            )

        try:
            response = requests.get(
                _OPENWEATHER_URL,
                params={
                    "q": self.settings.weather_location,
                    "appid": self.settings.weather_api_key,
                    "units": "imperial",
                },
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            logger.exception("Weather lookup failed.")
            raise WeatherProviderError("Could not reach the weather service.") from error

        data = response.json()
        try:
            return WeatherReport(
                location=data.get("name", self.settings.weather_location),
                description=data["weather"][0]["description"],
                temperature_f=data["main"]["temp"],
                feels_like_f=data["main"]["feels_like"],
                humidity_percent=data["main"]["humidity"],
            )
        except (KeyError, IndexError) as error:
            raise WeatherProviderError("Unexpected response from the weather service.") from error
