from state_machine.state_machine.state import State
from messages.msg import PIDInput
import time

class GoThroughSlalomState(State):
    def __init__(self):
        super().__init__('go_through_slalom')
        
        self.start_yaw : float | None = None
        self.start_time : float | None = None

        self.desired_depth : float | None = None
        
    def start(self, context : dict):
        self.start_yaw = 0.0 # context['odom']['yaw']
        self.start_time = time.time()
        self.desired_depth = context['gate_state_depth']
        self.x_power = context['slalom_forward_power']
        self.total_time = context['slalom_forward_time']
        
    def execute(self, context : dict):
        if time.time() - self.start_time >= self.total_time:
            return 'end_state'
        
        msg = PIDInput()
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.x_power = self.x_power
        
        msg.z_setpoint = self.desired_depth
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = self.start_yaw
        
        msg.z_measurement = context['depth']
        msg.roll_measurement = context['odom']['roll']
        msg.pitch_measurement = context['odom']['pitch']
        msg.yaw_measurement = context['odom']['yaw']
        
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        