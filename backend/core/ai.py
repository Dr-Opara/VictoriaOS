from openai import OpenAI

from backend.config.settings import get_settings
from backend.core.logger import logger


class AIGateway:
    """Gateway for Victoria's OpenAI GPT responses."""

    def __init__(self) -> None:
        self.settings = get_settings()

        self.client = OpenAI(
            api_key=self.settings.openai_api_key
        )

    DEFAULT_INSTRUCTIONS = """
You are Victoria, Dr. Opara's private executive AI assistant.

Rules:
- Never say you are ChatGPT or OpenAI.
- Always introduce yourself as Victoria.
- Address the user as Dr. Opara.
- Keep responses professional and concise.
""".strip()

    def ask(self, prompt: str, instructions: str | None = None) -> str:
        """Send a prompt to GPT and return the generated text.

        ``instructions`` defaults to Victoria's base persona. Callers that
        build a full context-aware prompt (see ``backend.core.context``) may
        pass ``instructions=""`` since the persona is already embedded.
        """
        try:
            response = self.client.responses.create(
                model=self.settings.model,
                instructions=self.DEFAULT_INSTRUCTIONS if instructions is None else instructions,
                input=prompt,
            )
        except Exception:
            logger.exception("OpenAI response generation failed.")
            raise

        return response.output_text
