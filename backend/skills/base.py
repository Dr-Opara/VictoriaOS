from abc import ABC, abstractmethod


class Skill(ABC):
    """
    Base class for every Victoria skill.
    """

    name: str

    @abstractmethod
    def execute(self, command: str):
        pass