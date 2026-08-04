from backend.skills.base import Skill


class CalendarSkill(Skill):

    name = "calendar"

    def execute(self, command: str):

        return {
            "skill": self.name,
            "message": "Calendar module is ready.",
            "command": command,
        }