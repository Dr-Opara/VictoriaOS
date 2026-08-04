from __future__ import annotations

import email
import html
import imaplib
import logging
import os
import re
from collections.abc import Iterable
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr

from dotenv import load_dotenv

from backend.integrations.email.models import (
    EmailConfigurationError,
    EmailMessage,
    EmailProviderError,
    YahooMailConfig,
)

load_dotenv()

logger = logging.getLogger("VictoriaOS")


class YahooMail:
    """Yahoo Mail IMAP provider for VictoriaOS."""

    DEFAULT_LIMIT = 10
    PREVIEW_LIMIT = 240

    def __init__(self, config: YahooMailConfig | None = None) -> None:
        self.config = config or self._config_from_environment()

    @classmethod
    def _config_from_environment(cls) -> YahooMailConfig:
        """Build Yahoo Mail configuration from environment variables."""
        username = os.getenv("YAHOO_EMAIL", "").strip()
        app_password = os.getenv("YAHOO_APP_PASSWORD", "").strip()
        imap_server = os.getenv("YAHOO_IMAP_SERVER", "imap.mail.yahoo.com").strip()
        mailbox = os.getenv("YAHOO_MAILBOX", "INBOX").strip()

        if not username or not app_password:
            raise EmailConfigurationError(
                "Yahoo Mail is not configured. Set YAHOO_EMAIL and "
                "YAHOO_APP_PASSWORD in the environment."
            )

        return YahooMailConfig(
            username=username,
            app_password=app_password,
            imap_server=imap_server,
            mailbox=mailbox,
        )

    def _connect(self) -> imaplib.IMAP4_SSL:
        """Connect and authenticate to Yahoo Mail over IMAP SSL."""
        logger.info("Connecting to Yahoo Mail IMAP as %s", self.config.username)

        try:
            connection = imaplib.IMAP4_SSL(self.config.imap_server)
            connection.login(self.config.username, self.config.app_password)
            return connection
        except imaplib.IMAP4.error as exc:
            logger.exception("Yahoo Mail authentication failed.")
            raise EmailProviderError("Yahoo Mail authentication failed.") from exc
        except OSError as exc:
            logger.exception("Unable to connect to Yahoo Mail IMAP.")
            raise EmailProviderError("Unable to connect to Yahoo Mail.") from exc

    def read_unread(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Return unread messages from the configured Yahoo mailbox."""
        return self._fetch_by_criterion("UNSEEN", limit)

    def read_latest(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Return the latest messages from the configured Yahoo mailbox."""
        return self._fetch_by_criterion("ALL", limit)

    def search(self, query: str, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Search Yahoo Mail using a broad subject/body/from IMAP query."""
        normalized_query = query.strip()
        if not normalized_query:
            return self.read_latest(limit=limit)

        escaped_query = normalized_query.replace("\\", "\\\\").replace('"', '\\"')
        criterion = f'(OR OR FROM "{escaped_query}" SUBJECT "{escaped_query}" BODY "{escaped_query}")'
        return self._fetch_by_criterion(criterion, limit)

    def unread_emails(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Backward-compatible alias for unread email reads."""
        return self.read_unread(limit=limit)

    def latest_emails(self, limit: int = DEFAULT_LIMIT) -> list[EmailMessage]:
        """Backward-compatible alias for latest email reads."""
        return self.read_latest(limit=limit)

    def _fetch_by_criterion(self, criterion: str, limit: int) -> list[EmailMessage]:
        """Fetch messages matching an IMAP search criterion."""
        limit = max(1, limit)
        connection = self._connect()

        try:
            status, _ = connection.select(self.config.mailbox, readonly=True)
            if status != "OK":
                raise EmailProviderError(
                    f"Unable to select Yahoo mailbox {self.config.mailbox!r}."
                )

            status, messages = connection.search(None, criterion)
            if status != "OK":
                raise EmailProviderError("Yahoo Mail search failed.")

            email_ids = messages[0].split()
            selected_ids = list(reversed(email_ids[-limit:]))
            logger.info(
                "Yahoo Mail returned %s messages for criterion %s.",
                len(selected_ids),
                criterion,
            )

            return self._fetch_messages(connection, selected_ids)
        except imaplib.IMAP4.error as exc:
            logger.exception("Yahoo Mail IMAP operation failed.")
            raise EmailProviderError("Yahoo Mail operation failed.") from exc
        finally:
            self._logout(connection)

    def _fetch_messages(
        self,
        connection: imaplib.IMAP4_SSL,
        email_ids: Iterable[bytes],
    ) -> list[EmailMessage]:
        """Fetch and normalize full RFC822 messages for the given ids."""
        messages: list[EmailMessage] = []

        for email_id in email_ids:
            status, message_data = connection.fetch(email_id, "(RFC822)")
            if status != "OK":
                logger.warning("Skipping Yahoo Mail message %s after fetch failure.", email_id)
                continue

            for response in message_data:
                if not isinstance(response, tuple):
                    continue

                parsed_message = email.message_from_bytes(response[1])
                messages.append(self._parse_message(parsed_message))
                break

        return messages

    def _parse_message(self, message: Message) -> EmailMessage:
        """Convert a raw email message into VictoriaOS metadata."""
        sender_name, sender_address = parseaddr(message.get("From", ""))
        sender = self._decode_header(sender_name) or sender_address or "Unknown sender"

        return EmailMessage(
            sender=sender,
            subject=self._decode_header(message.get("Subject", "")) or "(No subject)",
            date=message.get("Date", "Unknown date"),
            preview=self._extract_preview(message),
        )

    def _extract_preview(self, message: Message) -> str:
        """Extract a normalized plain-text preview from an email message."""
        body = self._extract_body(message)
        preview = re.sub(r"\s+", " ", body).strip()

        if len(preview) > self.PREVIEW_LIMIT:
            return f"{preview[: self.PREVIEW_LIMIT - 3].rstrip()}..."

        return preview or "(No preview available)"

    def _extract_body(self, message: Message) -> str:
        """Return the best plain-text body available for a message."""
        if message.is_multipart():
            html_fallback = ""

            for part in message.walk():
                content_disposition = part.get_content_disposition()
                if content_disposition == "attachment":
                    continue

                content_type = part.get_content_type()
                text = self._decode_part_payload(part)

                if content_type == "text/plain" and text:
                    return text
                if content_type == "text/html" and text and not html_fallback:
                    html_fallback = self._strip_html(text)

            return html_fallback

        text = self._decode_part_payload(message)
        if message.get_content_type() == "text/html":
            return self._strip_html(text)

        return text

    @staticmethod
    def _decode_header(value: str | None) -> str:
        """Decode an RFC 2047 header into readable text."""
        if not value:
            return ""

        try:
            return str(make_header(decode_header(value))).strip()
        except (LookupError, UnicodeDecodeError, ValueError):
            logger.warning("Unable to decode email header value.")
            return value.strip()

    @staticmethod
    def _decode_part_payload(part: Message) -> str:
        """Decode a message body part using its declared charset when present."""
        payload = part.get_payload(decode=True)
        if payload is None:
            raw_payload = part.get_payload()
            return raw_payload if isinstance(raw_payload, str) else ""

        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            return payload.decode("utf-8", errors="replace")

    @staticmethod
    def _strip_html(value: str) -> str:
        """Remove simple HTML markup for preview generation."""
        no_scripts = re.sub(
            r"<(script|style).*?</\1>",
            " ",
            value,
            flags=re.IGNORECASE | re.DOTALL,
        )
        no_tags = re.sub(r"<[^>]+>", " ", no_scripts)
        return html.unescape(no_tags)

    @staticmethod
    def _logout(connection: imaplib.IMAP4_SSL) -> None:
        """Close an IMAP connection without masking the original failure."""
        try:
            connection.logout()
        except imaplib.IMAP4.error:
            logger.warning("Yahoo Mail logout failed.", exc_info=True)
