import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from context import Context

class GoToDepthState(State):
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset", "complete"])
        self.context = context
        
        self.desired_depth = 1.0 # Meters
        
        
        
    def execute(self, bb: Blackboard):
        """
        Executes the logic for the Pole Alignment state.

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        # if depth != desired depth : go to depth
        
        if (True):
            return "next_state"