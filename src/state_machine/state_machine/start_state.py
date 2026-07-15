from state_machine.state import State
from messages.msg import PIDInput
import time

class StartState(State):
    def __init__(self):
        super().__init__('start')
        self.depth_threshold = None
        self.depth_time = None
        self.start_time = None
        
        self.wait_time = None
        
    def start(self, context : dict):
        self.depth_threshold = context['start_depth_threshold']
        self.depth_time = context['start_time']
        
        self.start_time = None
        
        self.wait_time = time.time()
        self.wait_time_threshold = context['start_wait_time']
        
        
    def execute(self, context : dict):
        if time.time() - self.wait_time >= self.wait_time_threshold and context['depth'] is not None and context['depth'] >= self.depth_threshold:
            if self.start_time is None:
               self.start_time = time.time()
            elif time.time() - self.start_time >= self.depth_time:
                return 'gate_go_to_depth'
        else:
            self.start_time = None
                 
        msg = PIDInput()
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        