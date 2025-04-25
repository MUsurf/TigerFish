class Task:
    def __init__(self, type : str):
        self.type = type
        #Progress Variables
        self.isComplete : bool = False
        self.isActive : bool = False
        self.attempted : bool = False
        #idks
        self.error : int = 0
        self.output : None = None 
        
    def execute(self, i): #-> output // What is "i" bro
        if (self.isComplete == True):
            return #We did, we don't need to be here
        
        if (self.isActive == True):
            #We are mid doing it, keep doing it
            #THIS GOES SOMEWHERE, NEED SURFBOARD I THINK
            #state = SurfBoard
            pass
        
        if (self.attempted == True):
            #We already tried but aren't complete --> failure
            if (self.error != 0):
                #Handle error? Or is this supervisor's job
                pass
        else:
            #start doing it, this must be first call?
            pass
        
        
        
        
        
        
        
        #process(state) -> action
        
        #return action, ChillVibes