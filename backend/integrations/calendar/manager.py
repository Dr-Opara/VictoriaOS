class CalendarManager:

    def __init__(self):
        self.providers = {}

    def register(self, name, provider):
        self.providers[name] = provider

    def provider(self, name):
        return self.providers.get(name)