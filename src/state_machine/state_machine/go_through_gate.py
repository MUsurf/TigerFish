from state_machine.state import State
from messages.msg import PIDInput
import time

class GoThroughGateState(State):
    def __init__(self):
        super().__init__('go_through_gate')
        
        self.start_yaw : float | None = None
        self.start_time : float | None = None

        self.desired_depth : float | None = None
        self.x_power = None
        self.total_time = None
        
    def start(self, context : dict):
        self.start_yaw = 0.0 # context['odom']['yaw']
        self.start_time = time.time()
        self.desired_depth = context['post_roll_depth']
        self.x_power = context['gate_forward_power']
        self.total_time = context['gate_forward_time']
        
    def execute(self, context : dict):
        if time.time() - self.start_time >= self.total_time:
            return 'go_up'
        
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
        
        
        