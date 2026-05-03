import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from context import Context

class ResetState(State):
    """
    State machine defaults to this state when the sub is above water. Essentially, do nothing.

    Outcomes:
        next_state: Restarts state machine; goes to the gate alignment state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state"])
        context = context
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the reset state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Reset")
        
        depth = bb.get("depth")
        
        # Construct PID message
        msg = PIDInput()

        # Do nothing!
        msg.z_power = 0
        msg.x_power = 0
        msg.y_power = 0
        msg.yaw_power = 0
        msg.pitch_power = 0
        msg.roll_power = 0
        
        # Underwater check
        if (depth > 0):
            return "next_state"
    