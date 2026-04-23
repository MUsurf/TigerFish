import time

import rclpy

import yasmin
from yasmin import State

class TokyoDrift(State):
    """
    State we boot to in the state machine.
    """
    def __init__(self) -> None:
        """
        Initializes the StartState instance, setting up the outcomes.

        Outcomes:
            outcome1: Indicates the state should continue to the Gate state.
            outcome2: Indicates the state should finish execution and return.
        """
        super().__init__(["outcome1", "outcome2"])
        self.set_description(
            "Ensures proper boot, transitions to Gate state or checks fails and we quit?"
        )
        
        
    def execute(self, blackboard: Blackboard):
        """
        Executes the logic for the Start state.

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state START")
        time.sleep(3)  # Simulate work by aw