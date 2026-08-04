from __future__ import annotations

import re
from typing import Any

from backend.core.ai import AIGateway
from backend.core.context import ContextBuilder
from backend.core.logger import logger
from backend.memory.service import MemoryService
from backend.profile.profile import UserProfile
from backend.skills.registry import SkillRegistry

_RECALL_PATTERN = re.compile(r"what do you remember about me", re.IGNORECASE)
_REMEMBER_PATTERN = re.compile(r"^remember\s+(?:that\s+)?(?P<fact>.+)", re.IGNORECASE)


class VictoriaOrchestrator:
    """Coordinates memory, preferences, tasks, and GPT for every command."""

    def __init__(
        self,
        ai: AIGateway | None = None,
        memory: MemoryService | None = None,
        profile: UserProfile | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.ai = ai or AIGateway()
        self.memory = memory or MemoryService()
        self.profile = profile or UserProfile()
        self.skills = SkillRegistry()
        self.context = context_builder or ContextBuilder(memory=self.memory, profile=self.profile)

    def process(self, command: str, session_id: str = "default") -> dict[str, Any]:
        """Process a user command using persistent memory, preferences, and history."""
        normalized_command = command.strip()

        if _RECALL_PATTERN.search(normalized_command):
            response = self._recall_everything()
            self.context.record_turn(session_id, normalized_command, response)
            return {"assistant": "Victoria", "response": response}

        remember_match = _REMEMBER_PATTERN.match(normalized_command)
        if remember_match:
            response = self._remember(remember_match.group("fact"))
            self.context.record_turn(session_id, normalized_command, response)
            return {"assistant": "Victoria", "response": response}

        context = self.context.build(session_id=session_id)
        prompt = context.to_prompt(normalized_command)

        response = self.ai.ask(prompt, instructions="")
        self.context.record_turn(session_id, normalized_command, response)

        return {"assistant": "Victoria", "response": response}

    def _remember(self, fact: str) -> str:
        """Save a fact as either a structured preference or a free-form memory."""
        preference = UserProfile.parse_preference_command(f"remember {fact}")
        if preference:
            key, value = preference
            self.profile.set_preference(key, value)
            logger.info("Stored preference %s=%s", key, value)
            return f"Got it, Dr. Opara. I'll remember your {key} is {value}."

        self.memory.remember(key=fact.strip()[:255], value=fact.strip())
        logger.info("Stored free-form memory: %s", fact)
        return f"Got it, Dr. Opara. I'll remember that {fact.strip()}."

    def _recall_everything(self) -> str:
        """Build a natural-language summary of everything Victoria remembers."""
        preferences = self.profile.all_preferences()
        memories = self.memory.recent(limit=20)

        if not preferences and not memories:
            return "I don't have anything remembered about you yet, Dr. Opara."

        lines = ["Here is what I remember about you, Dr. Opara:"]
        for preference in preferences:
            lines.append(f"- Your {preference.key} is {preference.value}.")
        for memory in memories:
            lines.append(f"- {memory.value}")

        return "\n".join(lines)
