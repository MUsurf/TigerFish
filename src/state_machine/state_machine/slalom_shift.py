from state_machine.state_machine.state import State
from messages.msg import PIDInput
import time

class SlalomShiftState(State):
    def __init__(self):
        super().__init__('slalom_shift')
        
    def start(self, context : dict):
        self.shift_time = context["slalom_shift_time"] 
        self.shift_power = context["slalom_shift_power"] 
        self.shift_direction = context["slalom_shift_direction"] 
        self.do_shift = context["do_shift"]
        
        self.start_time = time.time()
        
        
    def execute(self, context : dict):
        if self.do_shift : return 'go_through_slalom'
        if time.time() - self.start_time >= self.shift_time : return 'go_through_slalom'
                 
        msg = PIDInput()
        
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.y_power = self.shift_power * self.shift_direction
        
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
        
        
        