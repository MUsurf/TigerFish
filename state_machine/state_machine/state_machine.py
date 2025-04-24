from input_output import SurfBoard, Outputs
from supervisor import Supervisor
from task import Task
import time

class StateMachine:
    def __init__(self):
        self.publisher : None = None # Make this a ROS publisher 
        self.tasks : list = [None]
        self.current_task : int = 0
        self.last_error = None
        self.MAX_ERROR_TIME = 5
        
        # Tasks adding here
        
        self.surf_board : SurfBoard = SurfBoard()
        self.supervisor : Supervisor = Supervisor()
        
    def execute(self) -> None:
        output : Outputs = self.tasks[self.current_task].execute(self.surf_board)
        output, bad_output = self.supervisor.check(output, self.surf_board)
        
        # Error handling
        if(bad_output):
            if self.last_error == None : self.last_error = time.time()
            
            elif(time.time() - self.last_error >= self.MAX_ERROR_TIME):
                #Prob should be adjusted
                self.tasks[self.current_task].kill()
                self.current_task = 0
                self.last_error = None
        else:
            self.last_error = None
            
        self.publisher.publish(output)
        
         