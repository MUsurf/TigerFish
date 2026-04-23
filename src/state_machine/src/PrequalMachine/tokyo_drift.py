import time

import rclpy

import yasmin
from yasmin import State

class TokyoDrift(State):
    """
    Move around pole
    """
    def __init__(self) -> None:
        """
        Move around pole

        Outcomes:
            next_state: Go back to gate alignment
        """
        super().__init__(["next_state"])
        self.set_description(
            "Move around pole"
        )
        
        
    def execute(self, blackboard: Blackboard):
        """
        Executes the logic for the state.

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state TOKYO_DRIFT")
        gate = blackboard.get("pole_detection")
        odom = blackboard.get("odom")
        depth = blackboard.get("depth")

        while(True):
            
