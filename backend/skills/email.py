from backend.skills.base import Skill


class EmailSkill(Skill):

    name = "email"

    def execute(self, command: str):

        return {
            "skill": self.name,
            "message": "Email module is ready.",
            "command": command,
        }