import pytest

from backend.integrations.weather.models import WeatherConfigurationError, WeatherProviderError
from backend.integrations.weather.service import WeatherService


def test_is_configured_false_without_key():
    service = WeatherService()
    service.settings.weather_api_key = ""
    service.settings.weather_location = ""
    assert service.is_configured is False


def test_is_configured_true_with_key_and_location():
    service = WeatherService()
    service.settings.weather_api_key = "test-key"
    service.settings.weather_location = "Houston"
    assert service.is_configured is True


def test_current_raises_when_unconfigured():
    service = WeatherService()
    service.settings.weather_api_key = ""
    service.settings.weather_location = ""

    with pytest.raises(WeatherConfigurationError):
        service.current()


def test_current_raises_provider_error_on_bad_response(monkeypatch):
    service = WeatherService()
    service.settings.weather_api_key = "test-key"
    service.settings.weather_location = "Houston"

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"unexpected": "shape"}

    monkeypatch.setattr(
        "backend.integrations.weather.service.requests.get", lambda *a, **k: FakeResponse()
    )

    with pytest.raises(WeatherProviderError):
        service.current()


def test_current_parses_valid_response(monkeypatch):
    service = WeatherService()
    service.settings.weather_api_key = "test-key"
    service.settings.weather_location = "Houston"

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "name": "Houston",
                "weather": [{"description": "clear sky"}],
                "main": {"temp": 88.0, "feels_like": 92.0, "humidity": 55},
            }

    monkeypatch.setattr(
        "backend.integrations.weather.service.requests.get", lambda *a, **k: FakeResponse()
    )

    report = service.current()
    assert report.location == "Houston"
    assert report.temperature_f == 88.0
