from __future__ import annotations

import logging

from backend.core.ai import AIGateway
from backend.integrations.email.models import (
    EmailCategory,
    EmailConfigurationError,
    EmailMessage,
    EmailProviderError,
)
from backend.integrations.email.yahoo import YahooMail

logger = logging.getLogger("VictoriaOS")


class EmailService:
    """High-level email workflows for Victoria's executive assistant."""

    DEFAULT_LIMIT = 10

    def __init__(self, mail: YahooMail | None = None, ai: AIGateway | None = None) -> None:
        self._mail = mail
        self.ai = ai or AIGateway()

    def read_unread(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Read unread Yahoo Mail messages."""
        return self._get_mail().read_unread(limit=limit)

    def read_latest(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Read the latest Yahoo Mail messages."""
        return self._get_mail().read_latest(limit=limit)

    def search(self, query: str, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Search Yahoo Mail messages."""
        return self._get_mail().search(query=query, limit=limit)

    def _get_mail(self) -> YahooMail:
        """Return the configured Yahoo Mail provider."""
        if self._mail is None:
            self._mail = YahooMail()

        return self._mail

    def summarize_unread(self, limit: int = DEFAULT_LIMIT) -> str:
        """Summarize unread Yahoo Mail messages for Dr. Opara."""
        try:
            unread_messages = self.read_unread(limit=limit)
        except EmailConfigurationError:
            logger.exception("Email summary failed because Yahoo Mail is not configured.")
            return (
                "Victoria here, Dr. Opara. Yahoo Mail is not configured yet. "
                "Please set YAHOO_EMAIL and YAHOO_APP_PASSWORD so I can check "
                "your inbox."
            )
        except EmailProviderError:
            logger.exception("Email summary failed because Yahoo Mail could not be read.")
            return (
                "Victoria here, Dr. Opara. I could not read Yahoo Mail right now. "
                "Please check the mail connection and try again."
            )

        if not unread_messages:
            logger.info("No unread Yahoo Mail messages found.")
            return "Victoria here, Dr. Opara. You have no unread Yahoo emails."

        logger.info("Summarizing %s unread Yahoo Mail messages.", len(unread_messages))
        prompt = self._build_summary_prompt(unread_messages)

        try:
            return self.ai.ask(prompt)
        except Exception:
            logger.exception("GPT-5 email summarization failed.")
            return self._fallback_summary(unread_messages)

    def _build_summary_prompt(self, messages: list[EmailMessage]) -> str:
        """Build the GPT-5 prompt for executive email categorization."""
        categories = ", ".join(category.value for category in EmailCategory)
        formatted_messages = "\n\n".join(
            self._format_message_for_prompt(index, message)
            for index, message in enumerate(messages, start=1)
        )

        return f"""
You are Victoria, Dr. Opara's private executive AI assistant.

Summarize the unread Yahoo emails below as a natural-language executive briefing.
Categorize the messages into exactly these categories when relevant: {categories}.

Requirements:
- Start with a concise status sentence.
- Group the meaningful items by category.
- Call out anything urgent, financial, work-related, or requiring a reply.
- Mention senders and subjects when useful.
- Keep the tone professional, private, and concise.
- If a category has no relevant messages, omit it.

Unread emails:

{formatted_messages}
""".strip()

    @staticmethod
    def _format_message_for_prompt(index: int, message: EmailMessage) -> str:
        """Format a normalized email for GPT summarization."""
        return (
            f"{index}. Sender: {message.sender}\n"
            f"   Subject: {message.subject}\n"
            f"   Date: {message.date}\n"
            f"   Preview: {message.preview}"
        )

    def _fallback_summary(self, messages: list[EmailMessage]) -> str:
        """Return a deterministic summary if GPT summarization is unavailable."""
        lines = [
            (
                "Victoria here, Dr. Opara. I found unread Yahoo emails, but "
                "the AI summarizer is unavailable right now. Here are the latest "
                "items I could read:"
            )
        ]

        for message in messages:
            lines.append(
                f"- {message.sender}: {message.subject} "
                f"({message.date}) - {message.preview}"
            )

        return "\n".join(lines)
