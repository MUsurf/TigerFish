import math
import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class ThruGate(State):
    """
    Aligns the sub level to and facing the gate

    Outcomes:
        next_state: goes to the ???? state
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset", "obtain_depth"])
        self.context = context
        
        self.camera_separation = 0.075 # meters
        
        self.depth_range = 0.15     # meters
        self.desired_depth = 0.75   # meters
        
        self.began_past_time = 0.0
        self.past_time = 0.0
        self.blind_forward_time = 4.0
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Gate Alignment")
    
        # Get blackboard info
        pic1 = bb.get("pic1_detection") # TODO: Placeholder names, determine what info is actually in this topic
        pic2 = bb.get("pic2_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        
        
        if (self.role == 1): # placeholder, idk how we want to define this
            role_pic = pic1
        role_pic = pic2
        
        # Being out of the water is a reset trigger to stop all functions.
        if (depth < 0): # Does this need an offset?
            self.began_past_time = 0.0
            self.past_time = 0.0
            return "reset"
        
        # Achieve and maintain depth within desired range
        if (abs(depth - self.desired_depth) > self.depth_range):
            bb["prev_state"] = "thru_gate"
            return "obtain_depth"
        
        # Construct PID message, i.e. motor powers
        msg = PIDInput()
        
        msg.z_mode = True # True is PID enabled
        msg.x_mode = False # False is motor powers
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

        if (not role_pic["detected"]):
            msg.x_mode = True
            msg.x_power = 10.0
            
            if (self.began_past_time is None):
                self.began_past_time = time.time()
            else:
                self.past_time = time.time() - self.began_past_time
            
        elif (role_pic["detected"]):
            # Triangulate distances to role image
            distance = (self.camera_separation) / (math.tan(role_pic["x_l_ang"]) - math.tan(role_pic["x_r_ang"]))
            x_distance = (distance * math.tan(role_pic["x_l_ang"])) - (self.camera_separation / 2)
            y_distance = (distance * math.tan(role_pic["y_l_ang"])) # Andrew says use this but I don't believe him
            
            # Move forward toward image
            msg.x_measurement = 0.0
            msg.x_setpoint = distance
            # Keep centered with image
            msg.y_measurement = 0.0
            msg.y_setpoint = x_distance            
            
        self.context.pid_publisher.publish(msg)
        
        if (self.past_time > self.blind_forward_time):
            self.began_past_time = 0.0
            self.past_time = 0.0
            return "next_state"
        