from state_machine.state import State
from messages.msg import PIDInput
import time

class GoUpState(State):
    def __init__(self):
        super().__init__('go_up')
        self.start_time : float | None = None
        self.duration = None
        
    def start(self, context : dict):
        self.duration = context["go_up_time"]
        self.start_time = time.time()
        
    def execute(self, context : dict):
        if time.time() - self.start_time >= self.duration:
            return 'end'
        
        msg = PIDInput()
        msg.z_mode = False
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.z_power = -0.5
        
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = 0.0
        
        msg.roll_measurement = context['odom']['roll']
        msg.pitch_measurement = context['odom']['pitch']
        msg.yaw_measurement = context['odom']['yaw']
        
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        