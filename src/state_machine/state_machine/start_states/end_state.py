from yasmin import State, Blackboard
from messages.msg import PIDInput
import time

class StartState(State):
    def __init__(self, context : dict) -> None:
        super().__init__(outcomes = ["started"])
        self.context = context
        self.frequency = 5.0 # Hz
        
    def execute(self, bb : Blackboard):
        while True:
            st_t = time.time()            
            
            # Defaults to power mode, and 0 for everything.
            msg = PIDInput()
            self.context["pid_publisher"].publish(msg)
            
            time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))
        