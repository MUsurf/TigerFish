import time

import rclpy

import yasmin
from yasmin import State

class GoThroughGate(State):
    """
    We are already aligned to the gate
    Stay Straight and go forward until gate is cleared
    """
    def __init__(self) -> None:
        """
        stay aligned and go forward
        """
        super().__init__(["not_pole_danced", "pole_danced"])
        self.set_description(
            "Balances going forward and maintaining direction towards the center of the gate. Continues until gate has been cleared"
        )
        self.in_depth_start_time = 0
        self.is_in_depth = True
        self.sight_on_gate = True
        self.time_lost_sight = None
        
        
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
        half_sec_without_gate = False
        
        msg = PIDInput()
        msg.z_measurement = depth
        msg.z_setpoint = desired_depth
        msg.z_mode = True
        msg.z_power = 0
        
        # check if we lose sight of the gate for more than 2 seconds
        # if so, continue to next state
        if self.sight_on_gate == False:
            if self.time_lost_sight is None:
                self.time_lost_sight = time.time()
                
            elapsed = time.time() - self.time_lost_sight

            if elapsed >= 2:
                self.time_lost_sight = None
                return "not_pole_danced"
            elif elapsed >= 0.5:
                # Not a camera blip, stop and wait
                half_sec_without_gate = True
        else:
            self.time_lost_sight = None
        
        # check depth
        if (abs(depth - desired_depth) < 0.1):
            if not self.is_in_depth:
                self.is_in_depth = True
                self.in_depth_start_time = time.time()
            if time.time() - self.in_depth_start_time > 1.0: 
                msg.z_power = 0.1
        else:
            msg.z_power = 0
            self.is_in_depth = False
        
        #align to gate if not aligned, otherwise go forward
        if(self.gate_detection_x > 5):
            msg.y_power = -0.1
        elif(self.gate_detection_x < -5):
            msg.y_power = 0.1
        else:
            msg.y_power = 0
            
        
        if self.is_in_depth and not half_sec_without_gate:
            msg.x_power = 0.1
        else:
            msg.x_power = 0 #does this stop the sub?
            #Do I need to add something else to get the PID to do its thing?
        
        self.context.pid_publisher.publish(msg)
        
