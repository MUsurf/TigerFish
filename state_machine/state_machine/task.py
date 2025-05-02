from abc import ABC, abstractmethod
from adapterClasses import PID, Camera
import enum

class Task(ABC):
    def __init__(self, type : str):
        self.type = type
        
        # External Facing Task Progress Variables
        self.isComplete : bool = False
        self.isActive : bool = False
        self.wasAttempted : bool = False
        self.error : int = 0
        self.output : None = None 
        
        # Should enum "State" and currentState be here?
        
    @abstractmethod
    def execute(self):
        """
        Executes the task.
        
        This method should be overridden by subclasses to provide specific task behavior.
        It is designed to be called in a loop until the task is complete.
        The general structure should be a series of mutually exclusive if statements that check the current state of the task and execute the appropriate action.
        It may generally follow a linear flow but should be flexible enough to handle unexpected states or errors.
        """
        pass

class EnterGate(Task):
    
    # enums for tracking the internal task states
    class State(enum.Enum):
        """
        Enumeration representing the possible states of the system.
        Accessed in class via self.State.<state_name>
        The current state is stored in self.currentState

        States:
            seekingGate: The system is searching looking for the gate.
            aligningToGate: The system is aligning to center with gate and be within gate bounds.
            barrelRolling: The system is performing a barrel roll maneuver.
            movingThroughGate: The system is moving through the gate.
        """
        seekingGate = 1
        aligningToGate = 2
        barrelRolling = 3
        movingThroughGate = 4

    def __init__(self, type):
        """
        Initializes the EnterGate task.
            
        Internal Task Progress Variables:
            currentState: The current state of the system, initialized to seekingGate.
            barrelRollCount: The number of barrel rolls performed, initialized to 0.
            angleAllowance: The allowable angle for next barrel roll target, initialized to 5 degrees.
            currentAngleGoal: The target angle for the barrel roll, initialized to 10 degrees.
        """
        
        super().__init__(type)
        # Internal Task Progress Variables
        self.currentState : enum.Enum = self.State.seekingGate # Dr. Seuss
        
        # Track barrel roll progress
        # This is done by ensuring the roll angle continues to increase and incrementing the count when it rolls past 360 degrees
        self.barrelRollCount : int = 0
        self.angleAllowance : float = 5
        self.currentAngleGoal : float = 10

    
    def execute(self):
        """
        Executes the EnterGate task.
        """

        # If the task is not active, set it to active and start seeking the gate
        if self.isActive == False:
            self.isActive = True
            self.wasAttempted = True
            
            # In theory seekingGate should be initialized in init but if task is reset via isActive = False, it will be set to seekingGate
            # This may be necessary due to how states transition or may create issues
            self.currentState = self.State.seekingGate
            return
        
        # If seekingGate and the gate is not visible rotate to find it
        if self.currentState == self.State.seekingGate and not Camera.seeGate():
            
            PID.setVelocity(0, 0, 0, 0, 0, 5) # velocity
            return
        
        # If seekingGate and the gate is visible but not centered by angle, align to the gate
        # TODO: Should this be moved to aligningToGate?
        if self.currentState == self.State.seekingGate and not Camera.gateAlignedYaw():

            # this is a call to the PID to allign the robot to the gate
            PID.setVelocity(0, 0, 0, 0, 0, Camera.neededYaw()) # Both the PID call and Camera return may be position or velocity
            return
        
        # If seekingGate and the gate is visible but not centered by position, align to the gate
        # TODO: Should this be moved to aligningToGate?
        if self.currentState == self.State.seekingGate and not Camera.gateAlignedPosition():
            # Remember we want to align with a set half of the gate
            
            # this is a call to the PID to allign the robot to the gate
            PID.setVelocity(0, Camera.neededY(), 0, 0, 0, 0) # Both the PID call and Camera return may be position or velocity
            return

        # If seekingGate and the gate is visible and aligned, move onto state to align to the gate
        if self.currentState == self.State.seekingGate:
            
            self.currentState = self.State.aligningToGate # state change to start the process of going through the gate
            PID.stop() # short hand for PID.start(0, 0, 0, 0, 0, 0)
            return

        # If aligningToGate and we are not within the gate bounds, move towards the gate
        if self.currentState == self.State.aligningToGate and not Camera.gateAlignedDistance():
            
            PID.setVelocity(5, 0, 0, 0, 0, 0) # move towards gate also is velocity
            return

        # If aligningToGate and we are not aligned by yaw, align to the gate
        # TODO: Should this be moved to above the distance check?
        # TODO: As of now this may cause a deadlock if not aligned but moving towards the gate
        if self.currentState == self.State.aligningToGate and (not Camera.gateAlignedYaw() or not Camera.gateAlignedPosition()):
            
            self.currentState = self.State.seekingGate
            return
        
        # If aligningToGate and we are aligned, move onto state to barrel roll
        if self.currentState == self.State.aligningToGate:

            # If not done barrel rolling, move to barrel rolling state
            if(self.barrelRollCount < 3):

                self.currentState = self.State.barrelRolling

            # If done barrel rolling, move to movingThroughGate state
            else:

                self.currentState = self.State.movingThroughGate

            PID.stop()
            return
        
        # If barrelRolling and not enough rolls done keep rolling
        if self.currentState == self.State.barrelRolling and self.barrelRollCount < 3:
            
            # ! implement something that increases the velocity of the roll when the later check fails
            # Rotate to roll the submarine
            PID.setVelocity(0, 0, 0, 5, 0, 0) # velocity

            # Check if met next roll goal
            if self.currentAngleGoal < PID.subRollAngle() < self.currentAngleGoal + self.angleAllowance:
                
                # If so, increment the roll count and set the next goal
                self.currentAngleGoal = PID.subRollAngle() + self.angleAllowance

                # If have rolled past 360 degrees, reset the angle and increment the roll count
                if self.currentAngleGoal > 360:

                    self.currentAngleGoal = self.currentAngleGoal % 360

                    self.barrelRollCount += 1
                    
            return

        if self.currentState == self.State.barrelRolling:

            self.currentState = self.State.seekingGate
            return
        
        if self.currentState == self.State.movingThroughGate and Camera.seeGate():

            PID.setVelocity(5, 0, 0, 0, 0, 0) # velocity
            return
        

        if self.currentState == self.State.movingThroughGate:

            self.isComplete = True

            # if it gets to here, transition to another state
            # also, should we reset state here??? (aka put the vars back to their original)

        # if it gets to here, something bad happened as it failed all checks, which shoulnt happen
        self.error = 1
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