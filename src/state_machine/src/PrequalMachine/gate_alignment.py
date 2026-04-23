import time

import rclpy

import yasmin
from yasmin import State

class GateAlignment(State):
    """
    Is the starting state, and aligns to the gate
    """
    def __init__(self) -> None:
        """
        Is the starting state, and aligns to the gate

        Outcomes:
            outcome1: goes to the go through gate state
        """
        super().__init__(["next_state"])
        self.set_description(
            "Is the starting state, and aligns to the gate"
        )
        
        
    def execute(self, blackboard: Blackboard):
        """
        Executes the logic for the state

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state START")
        time.sleep(3)  # Simulate work by aw