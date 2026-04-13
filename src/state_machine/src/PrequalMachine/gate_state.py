import time

import rclpy

import yasmin
from yasmin import State

class GateState(State):
    """
    State to navigate through the gate. I want to use this state going in both directions!
    """
    def __init__(self, pid_publisher) -> None:
        """
        Initializes the GateState instance, setting up the outcomes.

        Outcomes:
            outcome1: Indicates the state should continue to the To_Pole state.
            outcome2: Indicates the state should finish execution and return.
        """
        super().__init__(["outcome1", "outcome2"])
        self.set_description(
            "Navigate sub through the prequalification gate from the surface of the water(?). Down and forward. Transition when through gate."
        )
    
    def execute(self, blackboard : Blackboard):    
        """
        Executes the logic for the Gate state.

        Args:
            blackboard (Blackboard): The shared data structure for states.

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state GATE")
        time.sleep(3)  # Simulate work by sleeping