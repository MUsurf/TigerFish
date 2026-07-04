from yasmin import State, Blackboard
from messages.msg import PIDInput
import time

class StartState(State):
    def __init__(self, context : dict) -> None:
        super().__init__(outcomes = ["started"])
        self.context = context
        self.time_in_water : float = 5.0
        self.underwater_threshold : float = 0.0
        self.underwater_start_time : float | None = None
        
        self.frequency = 5.0 # Hz
        
    def execute(self, bb : Blackboard):
        while True:
            st_t = time.time()
            depth : float = bb["depth"]
            
            if depth > self.underwater_threshold:
                if self.underwater_start_time is None:
                    self.underwater_start_time = time.time()
                elif time.time() - self.underwater_start_time >= self.time_in_water:
                    return "started"
            
            # Defaults to power mode, and 0 for everything.
            msg = PIDInput()
            self.context["pid_publisher"].publish(msg)
            
            time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))
        