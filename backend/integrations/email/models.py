from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EmailCategory(StrEnum):
    """Supported executive email summary categories."""

    IMPORTANT = "Important"
    WORK = "Work"
    BANKING = "Banking"
    SHOPPING = "Shopping"
    PROMOTIONS = "Promotions"


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """Normalized metadata returned by email providers."""

    sender: str
    subject: str
    date: str
    preview: str

    def to_prompt_dict(self) -> dict[str, str]:
        """Return a compact representation safe to pass into an AI prompt."""
        return {
            "sender": self.sender,
            "subject": self.subject,
            "date": self.date,
            "preview": self.preview,
        }


@dataclass(frozen=True, slots=True)
class YahooMailConfig:
    """Runtime configuration required to connect to Yahoo Mail."""

    username: str
    app_password: str
    imap_server: str = "imap.mail.yahoo.com"
    mailbox: str = "INBOX"


class EmailConfigurationError(RuntimeError):
    """Raised when email integration settings are missing or invalid."""


class EmailProviderError(RuntimeError):
    """Raised when an email provider cannot complete a requested operation."""
