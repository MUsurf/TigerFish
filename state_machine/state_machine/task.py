from abc import ABC, abstractmethod
from fakeClasses import PID, Camera
import enum

class Task(ABC):
    def __init__(self, type : str):
        self.type = type
        #Progress Variables
        self.isComplete : bool = False
        self.isActive : bool = False
        self.attempted : bool = False
        self.error : int = 0
        self.output : None = None 
        # maybe add the enum here instead?
        
    @abstractmethod
    def execute(self):
        pass

class EnterGate(Task):
    
    class State(enum.Enum): # enums for the internal task states
        seekingGate = 1
        movingTowardsGate = 2
        barrelRolling = 3
        movingThroughGate = 4

    def __init__(self, type):
        super().__init__(type)
        self.currentState : enum.Enum = self.State.seekingGate # Dr. Seuss
        self.barrelRollCount : int = 0
        self.angleAllowance : float = 5
        self.currentAngleGoal : float = 10

    
    def execute(self):

        if self.isActive == False:
            self.attempted = True
            self.currentState = self.State.seekingGate # this should in theory never matter, but maybe supervisor would make this be important
            self.isActive = True
            return
        
        if self.currentState == self.State.seekingGate and not Camera.seeGate():
            
            # this is for yaw, as it is x, y, z, roll, pitch, yaw
            # this is so we can find the gate as we arent facing it at the start
            PID.start(0, 0, 0, 0, 0, 5) # velocity
            return
        
        if self.currentState == self.State.seekingGate and not Camera.allignedYaw():

            # this is a call to the PID to allign the robot to the gate
            PID.start(0, 0, 0, 0, 0, Camera.neededYaw()) # position or velocity
            return
        
        if self.currentState == self.State.seekingGate and not Camera.allignedPosition():
            
            # this is a call to the PID to allign the robot to the gate
            PID.start(0, Camera.neededY(), 0, 0, 0, 0) # position or velocity
            return

        if self.currentState == self.State.seekingGate:
            
            self.currentState = self.State.movingTowardsGate # state change to start the process of going through the gate
            PID.stop() # short hand for PID.start(0, 0, 0, 0, 0, 0)
            return

        if self.currentState == self.State.movingTowardsGate and not Camera.withinWantedDistance():
            
            PID.start(5, 0, 0, 0, 0, 0) # move towards gate also is velocity
            return

        if self.currentState == self.State.movingTowardsGate and (not Camera.allignedYaw() or not Camera.allignedPosition()):
            
            self.currentState = self.State.seekingGate
            return
        
        if self.currentState == self.State.movingTowardsGate:

            if(self.barrelRollCount < 3):

                self.currentState = self.State.barrelRolling

            else:

                self.currentState = self.State.movingThroughGate

            PID.stop()
            return
        
        
        if self.currentState == self.State.barrelRolling and self.barrelRollCount < 3:
            
            # ! implement something that increases the velocity of the roll when the later check fails
            PID.start(0, 0, 0, 5, 0, 0) # velocity

            if self.currentAngleGoal < PID.subRollAngle() < self.currentAngleGoal + self.angleAllowance:
                
                self.currentAngleGoal = PID.subRollAngle() + self.angleAllowance

                if self.currentAngleGoal > 360:

                    self.currentAngleGoal = self.currentAngleGoal % 360

                    self.barrelRollCount += 1
            return

        if self.currentState == self.State.barrelRolling:

            self.currentState = self.State.seekingGate
            return
        
        if self.currentState == self.State.movingThroughGate and Camera.seeGate():

            PID.start(5, 0, 0, 0, 0, 0) # velocity
            return
        

        if self.currentState == self.State.movingThroughGate:

            self.isComplete = True

            # if it gets to here, transition to another state

            # also, should we reset state here??? (aka put the vars back to their original)

        # if it gets to here, something bad happened as it failed all checks, which shoulnt happen

        

        

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