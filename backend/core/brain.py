from backend.core.models import Intent


class VictoriaBrain:
    """
    Central decision engine.
    Every request passes through this class.
    """

    def classify(self, command: str) -> Intent:

        command = command.lower()

        if "email" in command:
            return Intent.EMAIL

        if "calendar" in command:
            return Intent.CALENDAR

        if "flight" in command:
            return Intent.TRAVEL

        if "weather" in command:
            return Intent.WEATHER

        if "bmw" in command:
            return Intent.BMW

        if "temperature" in command:
            return Intent.HOME

        if "call" in command:
            return Intent.PHONE

        return Intent.GENERAL