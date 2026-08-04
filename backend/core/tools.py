class ToolRegistry:
    """
    Registers all tools Victoria can use.
    """

    def __init__(self):
        self.tools = {}

    def register(self, name: str, tool):
        self.tools[name] = tool

    def get(self, name: str):
        return self.tools.get(name)

    def list_tools(self):
        return list(self.tools.keys())