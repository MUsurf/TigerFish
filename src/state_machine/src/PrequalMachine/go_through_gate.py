import time

import rclpy

import yasmin
from yasmin import State, Blackboard

from state_machine_node import Context
from context import Context

class GoThroughGate(State):
    """
    We are already aligned to the gate
    Stay Straight and go forward until gate is cleared
    """
    def __init__(self, context: Context) -> None:
        """
        stay aligned and go forward
        """
        super().__init__(["next_state", "reset"])
        self.set_description(
            "Balances going forward and maintaining direction towards the center of the gate. Continues until gate has been cleared"
        )
        # self.in_depth_start_time = 0
        # self.is_in_depth = True
        # self.sight_on_gate = True
        # self.time_lost_sight = None
        self.time_elapsed = None
        
        
        
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
        desired_depth = self.context.desired_depth
        self.sight_on_gate = gate["seen"]
        self.gate_detection_x= gate["x"]
        self.gate_detection_y = gate["y"]
        odom = bb.get("odom")
        # half_sec_without_gate = False
        
        msg = PIDInput()
        msg.z_measurement = depth
        msg.z_setpoint = desired_depth
        msg.z_mode = True
        msg.z_power = 0
        
        msg.yaw_setpoint = 0
        msg.yaw_measurement = odom["yaw"]
        msg.pitch_setpoint = 0
        msg.pitch_measurement = odom["pitch"]
        msg.roll_setpoint = 0
        msg.roll_measurement = odom["roll"]
        
        
        # Above water
        if (depth < 0):
            return "reset"
        
        
        if self.time_elapsed is not None:
            self.time_elapsed = time.time() - self.time_elapsed
            if self.time_elapsed > 7.0:
                self.time_elapsed = None
                msg.x_power = 0
                self.context.pid_publisher.publish(msg)
                return "next_state"
            
        
        msg.x_power = 0.4
            
        self.context.pid_publisher.publish(msg)
        
        # check if we lose sight of the gate for more than 2 seconds
        # if so, continue to next state
        
        # if self.sight_on_gate == False:
        #     if self.time_lost_sight is None:
        #         self.time_lost_sight = time.time()
                
        #     elapsed = time.time() - self.time_lost_sight

        #     if elapsed >= 2:
        #         self.time_lost_sight = None
        #         return "next_state"
        #     elif elapsed >= 0.5:
        #         # Not a camera blip, stop and wait
        #         half_sec_without_gate = True 
        # else:
        #     self.time_lost_sight = None
        #! ^^^^^^^
        #! The code above kinda misses the point a bit.
        #! If there is indeed no gate, but the CV blinks for 1 frame that there is, the code above does not catch that.
        #! This should more likely be a rolling average, so checking how many frames in the past X frames have been true vs false
        
        
        # check depth
        # if (abs(depth - desired_depth) < 0.1):
        #     if not self.is_in_depth:
        #         self.is_in_depth = True
        #         self.in_depth_start_time = time.time()
        #     if time.time() - self.in_depth_start_time > 1.0: 
        #         msg.z_power = 0.1
        # else:
        #     msg.z_power = 0
        #     self.is_in_depth = False
        #! You don't need any of this code. Raquel's state already checks that you stay in the desired depth, and from there, the PID Controller should handle it
        
        #align to gate if not aligned, otherwise go forward
        # if(self.gate_detection_x > 5):
        #     msg.y_power = -0.1
        # elif(self.gate_detection_x < -5):
        #     msg.y_power = 0.1
        # else:
        #     msg.y_power = 0
        #! Also probably don't need this?
        #! My though process for this would be that as you get close to the gate, CV signals get noisy since it is being cropped out of frame.
        #! So IMO I wouldn't worry about it, and would just focus on maintaining the current heading (0 yaw) and trust that Raquel set up the 
        #! right orientation
            