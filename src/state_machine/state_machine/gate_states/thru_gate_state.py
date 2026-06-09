import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class ThruGate(State):
    """
    Aligns the sub level to and facing the gate

    Outcomes:
        next_state: goes to the thru_gate state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset"])
        self.desired_depth = 0.75 # meters
        
        
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
        
        # Construct PID message, i.e. motor powers
        msg = PIDInput()