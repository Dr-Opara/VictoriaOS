from backend.core.ai import AIGateway


class VictoriaOrchestrator:
    """
    Central coordinator for VictoriaOS.
    Every request flows through this service.
    """

    def __init__(self):
        self.ai = AIGateway()

    def process(self, command: str):
        """
        Process a user command.
        Later this will:
        - Retrieve memory
        - Choose a skill
        - Call integrations
        - Use AI reasoning
        """
        return self.ai.ask(command)