from abc import ABC, abstractmethod

class State(ABC):
    def __init__(self, name):
        self.name = name
        
    @abstractmethod
    def start(self, context : dict) -> None:
        raise NotImplementedError("Bum you didn't implement start either!")
        
    @abstractmethod
    def execute(self, context : dict) -> str | None:
        raise NotImplementedError("Bum you didn't implement execute")
    
    
