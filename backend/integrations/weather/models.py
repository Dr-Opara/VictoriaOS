from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WeatherReport:
    """Normalized current-conditions weather data."""

    location: str
    description: str
    temperature_f: float
    feels_like_f: float
    humidity_percent: int

    def to_prompt_dict(self) -> dict[str, str]:
        """Return a compact representation safe to pass into an AI prompt."""
        return {
            "location": self.location,
            "description": self.description,
            "temperature_f": f"{self.temperature_f:.0f}",
            "feels_like_f": f"{self.feels_like_f:.0f}",
            "humidity_percent": f"{self.humidity_percent}",
        }


class WeatherConfigurationError(RuntimeError):
    """Raised when the weather provider's settings are missing or invalid."""


class WeatherProviderError(RuntimeError):
    """Raised when the weather provider cannot complete a requested operation."""
