from backend.skills.base import Skill


class EmailSkill(Skill):
    """Readiness skill for email-related commands."""

    name = "email"

    def execute(self, command: str) -> dict[str, str]:
        """Return a simple readiness response for email commands."""
        return {
            "skill": self.name,
            "message": "Email module is ready.",
            "command": command,
        }
