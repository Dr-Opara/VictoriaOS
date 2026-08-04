from __future__ import annotations

import logging
from collections.abc import Callable

from backend.integrations.email.yahoo import YahooMail

logger = logging.getLogger("VictoriaOS")

EmailProviderFactory = Callable[[], YahooMail]


class EmailManager:
    """Registry and factory for configured email providers."""

    def __init__(self) -> None:
        self._providers: dict[str, EmailProviderFactory] = {}
        self.register("yahoo", YahooMail)

    def register(self, name: str, provider_factory: EmailProviderFactory) -> None:
        """Register an email provider factory by name."""
        normalized_name = name.strip().lower()
        if not normalized_name:
            raise ValueError("Email provider name cannot be empty.")

        self._providers[normalized_name] = provider_factory
        logger.info("Registered email provider %s.", normalized_name)

    def provider(self, name: str) -> YahooMail | None:
        """Create a provider instance by name when registered."""
        provider_factory = self._providers.get(name.strip().lower())
        if provider_factory is None:
            return None

        return provider_factory()

    def providers_list(self) -> list[str]:
        """Return the registered email provider names."""
        return sorted(self._providers)
