from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backend.config.settings import get_settings
from backend.core.ai import AIGateway
from backend.core.logger import logger
from backend.integrations.calendar.service import CalendarService
from backend.integrations.email.models import EmailConfigurationError, EmailProviderError
from backend.integrations.email.service import EmailService
from backend.integrations.weather.models import WeatherConfigurationError, WeatherProviderError
from backend.integrations.weather.service import WeatherService
from backend.memory.service import MemoryService
from backend.task.manager import TaskManager
from backend.voice.tts import TextToSpeech

_BRIEFING_INSTRUCTIONS = """
You are Victoria, Dr. Opara's private executive AI assistant, delivering
his morning executive briefing.

Rules:
- Open with a personalized, time-appropriate greeting ("Good morning, Dr.
  Opara.").
- Cover, in order, only the sections that have data: today's schedule,
  weather, unread email highlights, tasks (call out anything overdue or
  due today first), and system status.
- If a section has no data or isn't configured, skip it silently - do not
  apologize for missing integrations in the briefing itself.
- Be concise and conversational, like a real executive assistant speaking
  out loud, not a bulleted report.
- Close with a short, forward-looking line (e.g. what needs attention
  first).
""".strip()


@dataclass
class BriefingContext:
    """Raw data gathered for the briefing, before GPT turns it into prose."""

    now: datetime
    calendar_events: list[dict] = field(default_factory=list)
    weather: dict | None = None
    unread_email_count: int = 0
    email_configured: bool = False
    pending_tasks: list[dict] = field(default_factory=list)
    overdue_task_count: int = 0
    system_notes: list[str] = field(default_factory=list)


def _format_task_line(task: dict) -> str:
    line = f"- {task['title']}"
    if task["priority"]:
        line += f" (priority: {task['priority']})"
    if task["due_at"]:
        line += f" (due {task['due_at']})"
    return line


class DailyBriefingService:
    """Assembles Victoria's executive daily briefing from every subsystem."""

    def __init__(
        self,
        ai: AIGateway | None = None,
        calendar: CalendarService | None = None,
        weather: WeatherService | None = None,
        email: EmailService | None = None,
        tasks: TaskManager | None = None,
        memory: MemoryService | None = None,
        tts: TextToSpeech | None = None,
    ) -> None:
        self.ai = ai or AIGateway()
        self.calendar = calendar or CalendarService()
        self.weather = weather or WeatherService()
        self.email = email or EmailService()
        self.tasks = tasks or TaskManager()
        self.memory = memory or MemoryService()
        self.tts = tts or TextToSpeech()
        self.settings = get_settings()

    def gather_context(self) -> BriefingContext:
        """Collect real data from every subsystem, degrading gracefully per-section."""
        now = datetime.now().astimezone()
        context = BriefingContext(now=now)

        context.calendar_events = [
            event.to_prompt_dict() for event in self.calendar.today_schedule(now=now)
        ]

        if self.weather.is_configured:
            try:
                context.weather = self.weather.current().to_prompt_dict()
            except (WeatherConfigurationError, WeatherProviderError):
                logger.warning("Briefing: weather lookup failed; omitting from briefing.")

        try:
            unread = self.email.read_unread(limit=10)
            context.email_configured = True
            context.unread_email_count = len(unread)
        except (EmailConfigurationError, EmailProviderError):
            context.email_configured = False

        pending = self.tasks.list_tasks(status="pending")
        context.pending_tasks = [
            {
                "title": task.title,
                "priority": task.priority,
                "due_at": task.due_at.isoformat() if task.due_at else None,
            }
            for task in pending
        ]
        context.overdue_task_count = len(self.tasks.due_tasks(now=now))

        context.system_notes.append(f"Model: {self.settings.model}")
        context.system_notes.append(f"Environment: {self.settings.environment}")

        return context

    def generate(self) -> str:
        """Generate the natural-language briefing text."""
        context = self.gather_context()
        prompt = self._build_prompt(context)
        return self.ai.ask(prompt, instructions=_BRIEFING_INSTRUCTIONS)

    def generate_audio(self, text: str | None = None, response_format: str = "mp3") -> bytes:
        """Synthesize the briefing (or any given text) as speech."""
        return self.tts.synthesize(text or self.generate(), response_format=response_format)

    @staticmethod
    def _build_prompt(context: BriefingContext) -> str:
        sections = [f"Current time: {context.now.strftime('%A, %B %d, %Y %I:%M %p %Z')}"]

        if context.calendar_events:
            lines = "\n".join(
                f"- {event['title']} at {event['start']}" for event in context.calendar_events
            )
            sections.append(f"Today's schedule:\n{lines}")
        else:
            sections.append("Today's schedule: nothing on the calendar.")

        if context.weather:
            sections.append(
                "Weather: "
                f"{context.weather['description']}, {context.weather['temperature_f']}F "
                f"(feels like {context.weather['feels_like_f']}F) in {context.weather['location']}."
            )

        if context.email_configured:
            sections.append(f"Unread email: {context.unread_email_count} messages.")

        if context.pending_tasks:
            lines = "\n".join(_format_task_line(task) for task in context.pending_tasks)
            sections.append(
                f"Pending tasks ({context.overdue_task_count} overdue):\n{lines}"
            )

        sections.append("System status: " + "; ".join(context.system_notes))

        return "\n\n".join(sections)
