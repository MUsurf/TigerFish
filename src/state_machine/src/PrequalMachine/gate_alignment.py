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
        in_depth_time = 0.0
        deep = True
        pause = 0.0
        
        
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
            while ((time.time() - self.pause) < 5.0):
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
            # Reset state and go on
            self.is_in_depth = False
            self.deep = False
            self.in_depth_time = 0
            return "next_state"