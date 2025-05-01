from abc import ABC, abstractmethod

class Task(ABC):
    def __init__(self, type : str):
        self.type = type
        #Progress Variables
        self.isComplete : bool = False
        self.isActive : bool = False
        self.attempted : bool = False
        self.error : int = 0
        self.output : None = None 
        
    @abstractmethod
    def execute(self):
        pass

class EnterGate(Task):
    def __init__(self, type):
        super().__init__(type)
    
    def execute(self):

        if self.isActive == False:

            self.isActive = True
            PID.beginRotationYaw()
            return
        
        if Camera.see_gate and not Camera.Alligned:
            
            if(Camera.hasSeenGate):

                PID.stopRotationYaw()

            PID.allignYaw(Camera.needed())
            return


        # while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #   move to align gate
        #   if gate_aligned:
        #       stop moving
        #       break
        # if not have_captured_image:
        #
        #   chose_gate = choose_gate()
        #
        #   capture_image()
        #
        #   process_and_store_image()
        #
        # have_captured_image = true
        #
        # while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #   move towards chose_gate
        #   if through_gate:
        #       stop moving
        #       break
        #
        # done

        return

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