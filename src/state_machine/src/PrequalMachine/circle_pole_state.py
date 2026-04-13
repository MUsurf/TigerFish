import time

import rclpy

import yasmin
from yasmin import State

class CirclePoleState(State):
    """
    State to circle the pole.
    """
    def __init__(self, pid_publisher) -> None:
        """
        Initializes the CirclePoleState instance, setting up the outcomes.

        Outcomes:
            outcome1: Indicates the state should continue to the FromPole state.
            outcome2: Indicates the state should finish execution and return.
        """
        super().__init__(["outcome1", "outcome2"])
        self.set_description(
            "Navigate sub in a circle around the pole, returning to initial position when the state began (level in front of the pole on the gate side).\n"
            + "Transitions when IMU registers we have completed a circle by returning to initial position."
        )
    
    def execute(self, blackboard: Blackboard):    
        """
        Executes the logic for the CirclePole state.

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state FROM_POLE")
        time.sleep(3)  # Simulate work by sleeping