from state_machine.state import State
from messages.msg import PIDInput
import time

class BarrelRollState(State):
    def __init__(self):
        super().__init__('barrel_roll')
        self.stable_time : float | None = None
        self.roll_power : float | None = None
        self.threshold : float | None = None
        
        self.accumulated_roll = None
        self.last_roll = None
        
        self.start_time = None
        
        self.temp_time = None
        
    def start(self, context : dict):
        self.start_time = None
        
        self.stable_time = context["barrel_roll_stable_time"]
        self.roll_power = context["barrel_roll_power"]
        self.threshold = context["barrel_roll_stable_threshold"]
        
        self.accumulated_roll = 0.0
        self.last_roll = None
        
    def execute(self, context : dict):
        msg = PIDInput()
        msg.pitch_mode = True
        msg.pitch_setpoint = 0.0
        msg.pitch_measurement = context['odom']['pitch']
        msg.roll_mode = True
        msg.roll_setpoint = 0.0
        msg.roll_measurement = context['odom']['roll']
        msg.z_setpoint = context['gate_state_depth']
        msg.z_measurement = context['depth']
        msg.z_mode = True
        if self.accumulated_roll > 570:
            msg.yaw_mode = True
            msg.yaw_setpoint = 0.0
            msg.yaw_measurement = context['odom']['yaw']

            if abs(context['odom']['yaw']) <= self.threshold:
                
                if self.start_time is None:
                    self.start_time = time.time()
                elif time.time() - self.start_time >= self.stable_time:
                    return 'gate_go_to_depth'
            else:
                self.start_time = None
        else:
            msg.yaw_mode = False
            msg.yaw_power = self.roll_power
        
        if self.last_roll is None:
            self.last_roll = context['odom']['yaw']
        else:
            self.accumulated_roll += abs(abs(self.last_roll) - abs(context['odom']['yaw']))
            self.last_roll = context['odom']['yaw']
        
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        