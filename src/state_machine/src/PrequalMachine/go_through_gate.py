import time

import rclpy

import yasmin
from yasmin import State

class GoThroughGate(State):
    """
    We are already aligned to the gate
    Stay Straight and go forward until gate is cleared
    """
    def __init__(self) -> None:
        """
        stay aligned and go forward

        Outcomes:
            outcome1 - tokyo drift has not ran yet
                continue to Pole Alignment
            outcome2 - tokyo drift has ran
                Finish program
        """
        super().__init__(["outcome1", "outcome2"])
        self.set_description(
            "Balances going forward and maintaining direction towards the center of the gate. Continues until gate has been cleared"
        )
        
        
    def execute(self, bb: Blackboard):
        """
        Executes the logic for the Go Through Gate state

        Returns: next_state

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state GoThroughGate")
        gate = bb.get("gate_detection")
        depth = bb.get("depth")
        desired_depth = bb.get("desired_depth")
        send = False
        
        msg = PIDInput()
        
        #cannot detect gate
        if gate[0] == False:
            return "next state"
        if (depth != desired_depth):
            msg.z_measurement = depth
            msg.z_setpoint = desired_depth
        #TODO: add something here for gate alignment
        msg.x_power = 10 #go forward?
        self.context.pid_publisher.publish(msg)
        
