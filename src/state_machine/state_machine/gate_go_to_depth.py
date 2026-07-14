from state_machine.state import State
from messages.msg import PIDInput
import time

class GateGoToDepthState(State):
    def __init__(self):
        super().__init__('gate_go_to_depth')
        
        self.start_yaw : float | None = None
        self.start_time : float | None = None

        self.desired_depth : float | None = None
        self.tolerance : float | None = None
        self.time_in_depth_requirement : float | None = None
        
    def start(self, context : dict):
        self.start_yaw = 0.0 # context['odom']['yaw']
        self.start_time = None
        
        self.desired_depth = context['gate_state_depth']
        self.tolerance = context['depth_error_tolerance']
        self.time_in_depth_requirement = context['time_in_depth_requirement']
        
    def execute(self, context : dict):
        if self.start_time is not None and time.time() - self.start_time >= self.time_in_depth_requirement:
            return 'go_through_gate'
        
        if abs(context['depth'] - self.desired_depth) <= self.tolerance:
            if self.start_time is not None:
                self.start_time = time.time()
        else:
            self.start_time = None
        
        msg = PIDInput()
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.z_setpoint = self.desired_depth
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = 0.0
        
        msg.z_measurement = context['depth']
        msg.roll_measurement = context['odom']['roll']
        msg.pitch_measurement = context['odom']['pitch']
        msg.yaw_measurement = context['odom']['yaw']
        
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        