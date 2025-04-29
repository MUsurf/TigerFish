from abc import ABC, abstractmethod

class Task(ABC):
    def __init__(self, type : str):
        self.type = type
        #Progress Variables
        self.isComplete : bool = False
        self.isActive : bool = False
        self.attempted : bool = False
        #idks
        self.error : int = 0
        self.output : None = None 
        
    @abstractmethod
    def execute(self): #-> output // What is "i" bro
        #         pass
        
        
        # if (self.isComplete == True):
        #     return #We did, we don't need to be here
        
        # elif (self.isActive == True):
            


        #     pass
        
        # elif (self.attempted == True):
        #     #We already tried but aren't complete --> failure
        #     if (self.error != 0):
        #         #Handle error? Or is this supervisor's job
        #         pass
        
        # else:
        #     #start doing it, this must be first call?
        #     pass
        
        
        pass

class EnterGate(Task):
    def __init__(self, type):
        super().__init__(type)
    
    def execute(self):
        
        # TODO do the stuff here 

        pass

class Slalom(Task):
    def __init__(self, type):
        super().__init__(type)
    
    def execute(self):
        
        # TODO do the stuff here 

        pass

class ExitGate(Task):
    def __init__(self, type):
        super().__init__(type)
    
    def execute(self):
        
        # TODO do the stuff here 

        pass
