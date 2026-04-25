import time

import rclpy

import yasmin
from yasmin import State

class GateAlignment(State):
    """
    Is the starting state. Aligns the sub level to and facing the gate

    Outcomes:
        next_state: goes to the go-through-gate state
    """
    def __init__(self) -> None:
        super().__init__(["next_state"])
        self.set_description(
            "Is the starting state. Aligns the sub level to and facing the gate"
        )
        
        
    def execute(self, blackboard: Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state START")
        gate = blackboard.get("gate_detection")
        odom = blackboard.get("odom")
        depth = blackboard.get("depth")

        if (depth != self.desired_depth):
            msg = PIDInput()
            # fill msg from blackboard data
            self.context.pid_publisher.publish(msg)
        elif (self.screen_center[0] != gate.x_pos and self.screen_center[1] != gate.y_pos):
            

        else:
            return "next_state"