import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class GateAlignment(State):
    """
    Is the starting state. Aligns the sub level to and facing the gate

    Outcomes:
        next_state: goes to the go-through-gate state
    """
    
    def __init__(self, Context : cntxt) -> None:
        super().__init__(["next_state"])
        context = cntxt
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Gate Alignment")
        
        # Get blackboard info
        gate = bb.get("gate_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        desired_depth = bb.get("desired_depth")
        
        # Construct PID message
        msg = PIDInput()
        msg.z_measurement = depth # Always maintain depth!
        msg.z_setpoint = desired_depth
        
        
        
        
        
        
        

        if (depth != desired_depth):
            
            send = True
        if (self.screen_center[0] != gate["x_pos"]): #  and self.screen_center[1] != gate["y_pos"] 
            # TODO: Figure smth out with camera vis to do pixel distances
            if ((self.screen_center[0] - gate["x_pos"]) > 0):
                msg.y_power = 5
            else:
                msg.y_power = -5 # Allowed?
            # msg.y_measurement = odom["y"]
            # msg.y_setpoint = gate["x_pos"] # Not sure this will work since it is perceived distance on a screen and not real?
            send = True
        else:
            msg.y_power = 0
        if (send):
            self.context.pid_publisher.publish(msg)
        else:
            return "next_state"