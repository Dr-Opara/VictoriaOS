class SkillRegistry:

    def __init__(self):
        self.skills = {}

    def register(self, name, skill):
        self.skills[name] = skill

    def get(self, name):
        return self.skills.get(name)

    def list(self):
        return list(self.skills.keys())