import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class ThruGate(State):
    """
    Aligns the sub level to and facing the gate

    Outcomes:
        next_state: goes to the ???? state
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset", "obtain_depth"])
        self.context = context
        
        self.depth_range = 0.15     # meters
        self.desired_depth = 0.75   # meters
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Gate Alignment")
        
        # Get blackboard info
        # gate = bb.get("gate_detection") ---- TODO: What get from CV here?
        odom = bb.get("odom")
        depth = bb.get("depth")
        
        # Being out of the water is a reset trigger to stop all functions.
        if (depth < 0): # Does this need an offset?
            return "reset"
        
        # Achieve and maintain depth within desired range
        if (abs(depth - self.desired_depth) > self.depth_range):
            bb["prev_state"] = "thru_gate"
            return "obtain_depth"
        
        # Construct PID message, i.e. motor powers
        msg = PIDInput()