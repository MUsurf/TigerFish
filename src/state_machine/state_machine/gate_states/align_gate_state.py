import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class AlignGate(State):
    """
    Aligns the sub level to and facing the gate based on the position of the role images.

    Outcomes:
        next_state: goes to the thru_gate state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset"])
        
        self.desired_depth = 0.75 # meters
        
        self.in_depth_time = 0 # Consecutive time spent at desired depth
        self.time_depth_reached = 0 # Time depth within range most recently reached
        
        self.role = context.role # Determines which side of the gate we go through/align with
        
        self.gate_centered_time = 0
        self.role_centered_time = 0
        self.time_entered = 0
        
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Gate Alignment")
        
        # Get blackboard info
        pic1 = bb.get("pic1_detection") # Placeholder names
        pic2 = bb.get("pic2_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        
        if (self.role is not 1):
            role_pic = pic2
        role_pic = pic1
        
        # Construct PID message, i.e. motor powers
        msg = PIDInput()
        
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True

        # Maintain depth and orientation
        msg.z_measurement = depth 
        msg.z_setpoint = self.desired_depth
        
        msg.yaw_setpoint = 0.0
        msg.measurement_yaw = odom["yaw"]
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        
        # Being out of the water is a reset trigger to stop all functions.
        if (depth < 0): # Does this need an offset?
            return "reset"
        
        # Achieve and maintain depth within desired range
        if (abs(depth - self.desired_depth) > 0.15):
            self.in_depth_time = 0
        if (abs(depth - self.desired_depth) < 0.15):
            if self.in_depth_time is 0:
                self.time_depth_reached = time.time()
            else:
                self.in_depth_time = time.time() - self.time_depth_reached
            
        # Align with gate
        if(self.in_depth_time > 3.0): # Must maintain depth for at least 3 seconds before proceeding
            
            # Center between both pictures
            if (not pic1["detected"] or not pic2["detected"]): #Spin until pictures spotted
                msg.yaw_setpoint = 5.0
            # moreeee
            
            
            # Move to one side to center with the designated role picture
            
            # if role_pic["detected"]:
            #     msg.yaw_setpoint = 0.0
            #     role_pic["x"] 
                 
                
                
                
                
        
        
        self.context.pid_publisher.publish(msg)
        
        if(self.in_depth_time > 3.0):
            # Reset state and go on
            self.is_in_depth = False
            self.deep = False
            self.in_depth_time = 0
            return "next_state"