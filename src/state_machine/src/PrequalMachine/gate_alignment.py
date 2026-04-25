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
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state START")
        gate = bb.get("gate_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        desired_depth = bb.get("desired_depth")
        send = False
        
        msg = PIDInput()

        if (depth != desired_depth):
            msg.z_measurement = depth
            msg.z_setpoint = desired_depth
            send = True
        if (self.screen_center[0] != gate["x_pos"]): #  and self.screen_center[1] != gate["y_pos"] 
            msg.y_measurement = odom["y"]
            msg.y_setpoint = gate["x_pos"] # Not sure this will work since it is perceived distance on a screen and not real?
            send = True
        if (send):
            self.context.pid_publisher.publish(msg)
        else:
            return "next_state"