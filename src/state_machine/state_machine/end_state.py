from state_machine.state_machine.state import State
from messages.msg import PIDInput
import time

DESIRED_DEPTH = 1 # meters
TOLERANCE = 0.075 # meters
TIME = 10.0 # seconds

class EndState(State):
    def __init__(self):
        super().__init__('end_state')
        
    def start(self, context : dict):
        return None
        
    def execute(self, context : dict):
        msg = PIDInput()
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        