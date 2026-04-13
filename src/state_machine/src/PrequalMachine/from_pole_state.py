import time

import rclpy

import yasmin
from yasmin import State

class FromPoleState(State):
    """
    State to navigate from the pole back to the gate.
    """
    def __init__(self, pid_publisher) -> None:
        """
        Initializes the ToPoleState instance, setting up the outcomes.

        Outcomes:
            outcome1: Indicates the state should continue to the Gate/ReverseGate state.
            outcome2: Indicates the state should finish execution and return.
        """
        super().__init__(["outcome1", "outcome2"])
        self.set_description(
            "Navigate sub from the pole to the prequalification gate. Keep the gate's central pole(?) in the center of forward camera until it is a certain size."
        )
    
    def execute(self, blackboard: Blackboard):    
        """
        Executes the logic for the FromPole state.

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state FROM_POLE")
        time.sleep(3)  # Simulate work by sleeping