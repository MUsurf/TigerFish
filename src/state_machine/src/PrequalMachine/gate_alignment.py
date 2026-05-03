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
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset"])
        context = context
        is_in_depth = False
        in_depth_time = 0
        deep = True
        pause = 0
        
        
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
        desired_depth = self.context.desired_depth
        
        # Construct PID message
        msg = PIDInput()
        
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True

        # Maintain depth and orientation
        msg.z_measurement = depth 
        msg.z_setpoint = desired_depth
        
        msg.yaw_setpoint = 0
        msg.yaw_measurement = odom["yaw"]
        msg.pitch_setpoint = 0
        msg.pitch_measurement = odom["pitch"]
        msg.roll_setpoint = 0
        msg.roll_measurement = odom["roll"]
        
        # Above water
        if (depth < 0):
            return "reset"
        
        # Wait to begin task
        if (self.pause == 0):
            self.pause = time.time()
            while ((time.time() - self.pause_) < 5.0):
                pass
        
        # Achieve and maintain desired depth within range 
        self.deep = False
        if (abs(depth - desired_depth) < 0.15):
            if not self.is_in_depth:
                self.is_in_depth = True
                self.in_depth_time = time.time()
            else:
                time_elapsed = time.time() - self.in_depth_time
                if (time_elapsed > 3.0):
                    self.deep = True
        else:
            self.is_in_depth = False
            
        # Align with gate
        # TODO: We don't have the CV for this at this time
        
        self.context.pid_publisher.publish(msg)
        
        if(self.deep):
            return "next_state"
        
        
        
        
        
        
        

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