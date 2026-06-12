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
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["next_state", "reset", "obtain_depth"])
        self.context = context
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
        
        msg.yaw_setpoint = odom["yaw"] # Is this zero?? Or do I make it equal zero
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
            bb["prev_state"] = "align_gate"
            return "obtain_depth"
            
        # Center between both pictures
        # This method assumes we start with enough distance from the gate for both pictures to be seen at once. Potentially bad?
        if (not pic1["detected"] or not pic2["detected"]): #Spin until pictures spotted
            msg.yaw_setpoint = 5.0
        else:
            msg.yaw_setpoint = 0
            # Distance to object = (focal length * distance between camera centers) / (difference between Xr and Xl in pixels)
            # The sub should be positioned perpendicular when Xr = Xl
            
        self.context.pid_publisher.publish(msg)
        
        return "next_state"