from input_output import SurfBoard, Outputs
from supervisor import Supervisor
from task import Task

class StateMachine:
    def __init__(self):
        self.publisher : None = None # Make this a ROS publisher 
        self.tasks : list = []
        self.surf_board : SurfBoard = SurfBoard()
        self.supervisor : Supervisor = Supervisor()
        
        