from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select

from backend.database.database import session_scope
from backend.database.models import ConversationHistory
from backend.memory.service import MemoryService
from backend.profile.profile import UserProfile
from backend.task.manager import TaskManager

DEFAULT_HISTORY_LIMIT = 10
DEFAULT_MEMORY_LIMIT = 20

SYSTEM_INSTRUCTIONS = """
You are Victoria, Dr. Opara's private executive AI assistant.

Rules:
- Never say you are ChatGPT or OpenAI.
- Always introduce yourself as Victoria.
- Address the user as Dr. Opara.
- Keep responses professional and concise.
- Use the remembered preferences, recent conversation, and open tasks below
  when they are relevant, but do not mention that you were "given context".
""".strip()


@dataclass
class AssistantContext:
    """Everything Victoria knows before answering: history, prefs, and tasks."""

    session_id: str
    history: list[ConversationHistory] = field(default_factory=list)
    preferences: dict[str, str] = field(default_factory=dict)
    open_tasks: list[str] = field(default_factory=list)
    memories: list[str] = field(default_factory=list)

    def to_prompt(self, command: str) -> str:
        """Render this context and the new command into a single GPT prompt."""
        sections = [SYSTEM_INSTRUCTIONS]

        if self.preferences:
            preference_lines = "\n".join(
                f"- {key}: {value}" for key, value in self.preferences.items()
            )
            sections.append(f"Known preferences:\n{preference_lines}")

        if self.memories:
            memory_lines = "\n".join(f"- {memory}" for memory in self.memories)
            sections.append(f"Remembered facts:\n{memory_lines}")

        if self.open_tasks:
            task_lines = "\n".join(f"- {task}" for task in self.open_tasks)
            sections.append(f"Open tasks:\n{task_lines}")

        if self.history:
            history_lines = "\n".join(
                f"Dr. Opara: {turn.user_message}\nVictoria: {turn.assistant_response}"
                for turn in reversed(self.history)
            )
            sections.append(f"Recent conversation:\n{history_lines}")

        sections.append(f"Dr. Opara: {command}")
        return "\n\n".join(sections)


class ContextBuilder:
    """Gathers conversation history, preferences, and tasks for every GPT call.

    All assistant-facing endpoints should build their prompt through this
    class instead of calling the AI gateway directly, so Victoria's answers
    are always grounded in what she already knows about Dr. Opara.
    """

    def __init__(
        self,
        memory: MemoryService | None = None,
        profile: UserProfile | None = None,
        tasks: TaskManager | None = None,
    ) -> None:
        self.memory = memory or MemoryService()
        self.profile = profile or UserProfile()
        self.tasks = tasks or TaskManager()

    def build(self, session_id: str = "default") -> AssistantContext:
        """Assemble the current context for a given conversation session."""
        return AssistantContext(
            session_id=session_id,
            history=self._recent_history(session_id),
            preferences={pref.key: pref.value for pref in self.profile.all_preferences()},
            open_tasks=[task.title for task in self.tasks.list_tasks(status="pending")],
            memories=[f"{memory.key}: {memory.value}" for memory in self.memory.recent(
                limit=DEFAULT_MEMORY_LIMIT
            )],
        )

    def record_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata_json: str = "{}",
    ) -> ConversationHistory:
        """Persist a completed user/assistant exchange."""
        db = session_scope()
        try:
            turn = ConversationHistory(
                session_id=session_id,
                user_message=user_message,
                assistant_response=assistant_response,
                metadata_json=metadata_json,
            )
            db.add(turn)
            db.commit()
            db.refresh(turn)
            return turn
        finally:
            db.close()

    @staticmethod
    def _recent_history(
        session_id: str, limit: int = DEFAULT_HISTORY_LIMIT
    ) -> list[ConversationHistory]:
        db = session_scope()
        try:
            statement = (
                select(ConversationHistory)
                .where(ConversationHistory.session_id == session_id)
                .order_by(ConversationHistory.created_at.desc())
                .limit(limit)
            )
            return list(db.scalars(statement))
        finally:
            db.close()
