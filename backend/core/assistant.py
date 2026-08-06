from __future__ import annotations

import logging
import re
from typing import Any

from backend.core.context import ContextBuilder
from backend.core.orchestrator import VictoriaOrchestrator
from backend.integrations.email.service import EmailService
from backend.knowledge.manager import KnowledgeManager

logger = logging.getLogger("VictoriaOS")

_KNOWLEDGE_PATTERN = re.compile(
    r"\b(my documents?|my files?|my notes?|according to (my|the) (document|file|notes))\b",
    re.IGNORECASE,
)


class VictoriaAssistant:
    """Top-level assistant interface used by the API and voice surfaces."""

    def __init__(
        self,
        orchestrator: VictoriaOrchestrator | None = None,
        email_service: EmailService | None = None,
        context_builder: ContextBuilder | None = None,
        knowledge_manager: KnowledgeManager | None = None,
    ) -> None:
        self.orchestrator = orchestrator or VictoriaOrchestrator()
        self.email = email_service or EmailService()
        self.context = context_builder or self.orchestrator.context
        self.knowledge = knowledge_manager or KnowledgeManager()

    def think(self, command: str, session_id: str = "default") -> dict[str, Any]:
        """Process a user command and return Victoria's response payload."""
        normalized_command = command.strip()
        logger.info("VictoriaAssistant received command: %s", normalized_command)

        if self._is_email_check_request(normalized_command):
            logger.info("Routing command to EmailService unread summary.")
            response = self.email.summarize_unread()
            self.context.record_turn(session_id, normalized_command, response)
            return {"assistant": "Victoria", "response": response}

        if self._is_knowledge_request(normalized_command):
            logger.info("Routing command to KnowledgeManager (RAG over documents).")
            result = self.knowledge.ask(normalized_command)
            self.context.record_turn(session_id, normalized_command, result.answer)
            return {"assistant": "Victoria", "response": result.answer, "sources": result.sources}

        return self.orchestrator.process(normalized_command, session_id=session_id)

    @staticmethod
    def _is_email_check_request(command: str) -> bool:
        """Return True when a command asks Victoria to check unread email."""
        normalized = command.lower()
        email_terms = ("email", "emails", "mail", "inbox")
        action_pattern = r"\b(check|read|summarize|summary|show|scan|review)\b"

        return any(term in normalized for term in email_terms) and bool(
            re.search(action_pattern, normalized)
        )

    @staticmethod
    def _is_knowledge_request(command: str) -> bool:
        """Return True when a command asks Victoria to consult ingested documents."""
        return bool(_KNOWLEDGE_PATTERN.search(command))
