import time

import rclpy

import yasmin
from yasmin import State

class PoleAlignment(State):
    """
    State to align with and go to pole.
    """
    def __init__(self) -> None:
        """
        Initializes the Pole Alignment instance, setting up the outcomes.

        Outcomes:
            next_state: goes to the circle-pole-state
        """
        super().__init__(["next_state"])
        
        
    def execute(self, bb: Blackboard):
        """
        Executes the logic for the Pole Alignment state.

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state Pole Alignment")
        pole = bb.get("pole_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        desired_depth = bb.get("desired_depth")
        send = False
        
        msg = PIDInput()
        
        # Maintain depth
        if (depth != desired_depth):
            msg.z_measurement = depth
            msg.z_setpoint = desired_depth
            send = True
            
        # Center pole
        if (self.screen_center[0] != pole["x_pos"]):
            # TODO: Figure smth out with camera vis to do pixel distances
            if ((self.screen_center[0] - pole["x_pos"]) > 0):
                msg.y_power = 5
            else:
                msg.y_power = -5 # Allowed?
            send = True
        if (odom.y_measurement != 0):
            msg.y_power = 0
            send = True
            
        # Go to pole
        # TODO: Use computer vis to keep a certain distance 
        
        if (send):
            self.context.pid_publisher.publish(msg)
        else:
            return "next_state"