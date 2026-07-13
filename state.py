from abc import ABC, abstractmethod

class State:
    def __init__(self, name):
        self.name = name
        
    @abstractmethod
    def execute(self, context : dict) -> None | str:
        raise NotImplementedError("Bum you didn't implement execute")
    
