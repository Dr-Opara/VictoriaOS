from openai import OpenAI

from backend.config.settings import get_settings

settings = get_settings()


class AIGateway:
    """
    Central gateway for all AI interactions.
    Every module in VictoriaOS will use this class instead of
    calling the OpenAI SDK directly.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def ask(self, prompt: str):
        """
        Placeholder implementation.
        We'll connect this to the OpenAI Responses API later.
        """
        return {
            "status": "ready",
            "prompt": prompt
        }