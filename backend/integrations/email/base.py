from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """
    Base class for all email providers.
    """

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def read_inbox(self):
        pass

    @abstractmethod
    def send_email(self, recipient, subject, body):
        pass

    @abstractmethod
    def search(self, query):
        pass