import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from state_machine_node import Context

class ObtainDepth(State):
    """
    Achieves and  maintains the desired depth of the sub.
    When transitioning to this state, prev state pushes its name to blackboard \"prev_state\" for return.

    Outcomes:
        Goes to whatever previous state it came from.
    """
    
    def __init__(self, context : Context) -> None:
        super().__init__(["align_gate", "thru_gate", "reset"])
        self.context = context
        self.desired_depth = 0.75   # meters
        self.depth_range = 0.15     # meters
        self.maintain_time = 3.0    # sec
        
        self.in_depth_time = 0 # Consecutive time spent at desired depth
        self.time_depth_reached = 0 # Time depth within range most recently reached
        
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the depth achieving and maintaing state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Obtain Depth")
        
        # Get blackboard info
        prev_state = bb.get("prev_state") # When transitioning to this state, prev state pushes its name to bb for return
        odom = bb.get("odom")
        depth = bb.get("depth")
        
        
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
        if (abs(depth - self.desired_depth) > self.depth_range):
            self.in_depth_time = 0
        if (abs(depth - self.desired_depth) < self.depth_range):
            if self.in_depth_time is None:
                self.time_depth_reached = time.time()
            else:
                self.in_depth_time = time.time() - self.time_depth_reached
                
        self.context.pid_publisher.publish(msg)
        
        # Reset state and go on after maintaing for at least three seconds
        if(self.in_depth_time > self.self.maintain_time):
            self.time_depth_reached = 0
            self.in_depth_time = 0
            return prev_state