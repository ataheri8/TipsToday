from abc import ABC, abstractmethod

class Context(ABC):

    @property
    @abstractmethod
    def db(self):
        pass

    @property
    @abstractmethod
    def redis(self):
        pass

    @property
    @abstractmethod
    def session(self):
        pass



