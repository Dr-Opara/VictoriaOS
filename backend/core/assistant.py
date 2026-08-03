from backend.core.brain import VictoriaBrain


class VictoriaAssistant:

    def __init__(self):

        self.brain = VictoriaBrain()

    def think(self, command: str):

        intent = self.brain.classify(command)

        return {
            "command": command,
            "intent": intent.value
        }