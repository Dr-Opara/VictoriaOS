from backend.core.briefing import DailyBriefingService
from backend.integrations.email.models import EmailConfigurationError
from backend.integrations.weather.models import WeatherConfigurationError


class FakeAIGateway:
    def ask(self, prompt, instructions=None):
        return f"BRIEFING::{prompt}"


class FakeCalendarService:
    def today_schedule(self, now=None):
        return []


class FakeWeatherService:
    is_configured = False

    def current(self):
        raise WeatherConfigurationError("not configured")


class FakeEmailService:
    def read_unread(self, limit=10):
        raise EmailConfigurationError("not configured")


class FakeTaskManager:
    def list_tasks(self, status=None):
        return []

    def due_tasks(self, now=None):
        return []


class FakeMemoryService:
    pass


class FakeTTS:
    def synthesize(self, text, response_format="mp3"):
        return b"FAKEAUDIO"


def _service() -> DailyBriefingService:
    return DailyBriefingService(
        ai=FakeAIGateway(),
        calendar=FakeCalendarService(),
        weather=FakeWeatherService(),
        email=FakeEmailService(),
        tasks=FakeTaskManager(),
        memory=FakeMemoryService(),
        tts=FakeTTS(),
    )


def test_gather_context_degrades_gracefully_when_nothing_configured():
    service = _service()
    context = service.gather_context()

    assert context.calendar_events == []
    assert context.weather is None
    assert context.email_configured is False
    assert context.pending_tasks == []


def test_generate_calls_ai_with_prompt_built_from_context():
    service = _service()
    text = service.generate()
    assert text.startswith("BRIEFING::")
    assert "Current time" in text


def test_generate_audio_synthesizes_the_briefing_text():
    service = _service()
    audio = service.generate_audio()
    assert audio == b"FAKEAUDIO"


def test_pending_tasks_and_weather_appear_in_prompt_when_available():
    class ConfiguredWeather:
        is_configured = True

        def current(self):
            class Report:
                def to_prompt_dict(self):
                    return {
                        "location": "Houston",
                        "description": "sunny",
                        "temperature_f": "90",
                        "feels_like_f": "95",
                        "humidity_percent": "40",
                    }

            return Report()

    class TaskWithPending:
        def list_tasks(self, status=None):
            class T:
                title = "Finish report"
                priority = "high"
                due_at = None

            return [T()]

        def due_tasks(self, now=None):
            return []

    service = DailyBriefingService(
        ai=FakeAIGateway(),
        calendar=FakeCalendarService(),
        weather=ConfiguredWeather(),
        email=FakeEmailService(),
        tasks=TaskWithPending(),
        memory=FakeMemoryService(),
        tts=FakeTTS(),
    )

    text = service.generate()
    assert "sunny" in text
    assert "Finish report" in text
