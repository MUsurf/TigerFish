import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from context import Context

class PoleAlignment(State):
    """
    State to align with and go to pole.
    """
    def __init__(self, context : Context) -> None:
        """
        Initializes the Pole Alignment instance, setting up the outcomes.

        Outcomes:
            next_state: goes to the circle-pole-state
        """
        super().__init__(["next_state", "reset", "complete"])
        context = context
        
        desired_alignment = 0.0
        time_aligned = 0.0
        time_at_pole = 0.0
        is_aligned = False
        aligned = False
        is_at_pole = False
        pole = False
        desired_depth = self.context.desired_depth
        desired_width = self.context.desired_width
        
        timer_back = 0.0
        back_time = 10.0
        returning = False
        
        
        
    def execute(self, bb: Blackboard):
        """
        Executes the logic for the Pole Alignment state.

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        # Get blackboard info
        pole = bb.get("pole_detection")
        odom = bb.get("odom")
        depth = bb.get("depth")
        y_angle = pole["yaw_angle"]
        width = pole["pixel_width"]
        
        # Construct PID message
        msg = PIDInput()
        
        msg.z_mode = True
        # msg.y_mode = True
        # msg.x_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True

        # Maintain depth and orientation
        msg.z_measurement = depth 
        msg.z_setpoint = self.desired_depth
        
        msg.y_power = 0
        
        msg.yaw_setpoint = 0
        msg.yaw_measurement = odom["yaw"]
        msg.pitch_setpoint = 0
        msg.pitch_measurement = odom["pitch"]
        msg.roll_setpoint = 0
        msg.roll_measurement = odom["roll"]
        
        # Above water
        if (depth < 0):
            return "reset"
        
        if (self.context.pole_danced == False):
            # Center pole
            self.aligned = False
            # Achieve and maintain alignment
            if (abs(y_angle - self.desired_alignment) < 0.5):
                if not self.is_aligned:
                    self.is_aligned = True
                    self.time_aligned = time.time()
                else:
                    time_elapsed = time.time() - self.time_aligned
                    if (time_elapsed > 3.0):
                        self.aligned = True
            elif ((y_angle - self.desired_alignment) < 0): # Scoot right
                self.is_aligned = False # Restart maintenance
                self.aligned = False
                self.time_aligned = 0
                msg.y_power = 0.1
            elif ((y_angle - self.desired_alignment) > 0): # Scoot left
                self.is_aligned = False
                self.aligned = False
                self.time_aligned = 0
                msg.y_power = -0.1

            # Go to pole
            if (self.aligned):
                if (abs(width - self.desired_width) < 5):
                    if not self.is_at_pole:
                        self.is_at_pole = True
                        self.time_at_pole = time.time()
                    else:
                        time_elapsed = time.time() - self.time_at_pole
                        if (time_elapsed > 3.0):
                            self.pole = True
                elif ((width - self.desired_width) < 0): # Scoot backward
                    self.is_at_pole = False
                    self.pole = False
                    self.time_at_pole = 0
                    msg.x_power = -0.1
                elif ((y_angle - self.desired_width) > 0): # Scoot forward
                    self.is_at_pole = False
                    self.pole = False
                    self.time_at_pole = 0
                    msg.x_power = 0.1
        # Return through gate
        else:
            if (self.time_back == 0.0):
                self.time_back = time.time()
                msg.y_power = 0.1
            else:
                time_elapsed = time.time() - self.time_back
                if (time_elapsed > self.time_back):
                    msg.y_power = 0

            
        self.context.pid_publisher.publish(msg)
        
        if (self.pole == True and self.aligned == True):
            return "next_state"