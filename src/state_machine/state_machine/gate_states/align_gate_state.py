import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class AlignGate(State):
    """
    Aligns the sub level to and facing the gate based on the position of the role images.

    Outcomes:
        next_state: goes to the align_role state
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
        face_gate: goes back to the face_gate state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset", "obtain_depth", "face_gate"])
        self.context = context
        self.role = context.role # Determines which side of the gate we go through/align with
        self.align_buffer = 0.15
        self.aligned_began_time = 0
        self.aligned_time = 0
        
        self.depth_range = 0.15     # meters
        self.desired_depth = 0.75   # meters
        
        
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
            
        
        x_l = pic1["X"] # TODO: Need to know what info, e.g., left cam X and right cam X for pic1 (x_1_L, x_1_R, x_2_L, x_2_R), etc
        x_r = pic2["X"]
    
        # In the event that both pictures are somehow lost, go back to spinning until seen
        if (not pic1["detected"] and not pic2["detected"]):
            self.aligned_began_time = 0
            self.aligned_time = 0
            return "face_gate"
        
        # Construct PID message, i.e. motor powers
        msg = PIDInput()
        
        msg.z_mode = True # True is PID enabled
        msg.y_mode = False # False is motor powers
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
            self.aligned_began_time = 0.0
            self.aligned_time = 0.0
            return "reset"
        
        # Achieve and maintain depth within desired range
        if (abs(depth - self.desired_depth) > self.depth_range):
            bb["prev_state"] = "align_gate"
            return "obtain_depth"
            
        # Center between both pictures
        # This method assumes we start with enough distance from the gate for both pictures to be seen at once. Potentially bad?

            # Distance to object = (focal length * distance between camera centers) / (difference between Xr and Xl in pixels)
            # The sub should be positioned perpendicular when Xr = Xl
            
            #TODO: Andrew will do the alignment with gate and correct side based on role
            
            if self.aligned_time is None: # Maintain facing for a few seconds before moving on to align to a side
                self.aligned_began_time = time.time()
            else:
                self.aligned_time = time.time() - self.aligned_began_time
            
        self.context.pid_publisher.publish(msg)
        
        if (self.aligned_time > self.align_buffer):
            self.aligned_began_time = 0
            self.aligned_time = 0
            return "next_state"