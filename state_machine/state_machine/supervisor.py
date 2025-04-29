from input_output import SurfBoard, Outputs
from task import Task
from state_machine import StateMachine

class Supervisor:
    
    def __init__(self):
        pass

    def check(self, output : Outputs, surf_board : SurfBoard):

        if(self.is_valid(output)):

            return (output, True)
        
        else:
            
            return (output, False)
    
    def is_valid(self, output : Outputs) -> bool:

        # todo - (maybe do camera later?) (maybe do collision check with accelerometer)

        timeBeforeCollision = 5 # the amount of seconds we look ahead before calling a kill on going up/down

        depthToBottom = 8 # depth to bottom of pool in feet

        if(output.y + output.yVelocity * timeBeforeCollision < 0 or output.y + output.yVelocity * timeBeforeCollision > depthToBottom):

            StateMachine.tasks[StateMachine.current_task].kill() # not sure if this python, but we ball

        return True

    def stopTask(self):
        pass