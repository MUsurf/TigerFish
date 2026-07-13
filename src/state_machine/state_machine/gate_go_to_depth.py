from state_machine.state_machine.state import State
from messages.msg import PIDInput
import time

DESIRED_DEPTH = 1 # meters
TOLERANCE = 0.075 # meters
TIME = 10.0 # seconds

class GateGoToDepthState(State):
    def __init__(self):
        super().__init__('go_to_depth_state')
        
        self.start_yaw : float | None = None
        self.start_time : float | None = None
        
    def start(self, context : dict):
        self.start_yaw = 0.0 # context['odom']['yaw']
        self.start_time = None
        
    def execute(self, context : dict):
        if self.start_time is not None and time.time() - self.start_time >= TIME:
            return 'go_through_gate'
        
        if abs(context['depth'] - DESIRED_DEPTH) <= TOLERANCE:
            if self.start_time is not None:
                self.start_time = time.time()
        else:
            self.start_time = None
        
        msg = PIDInput()
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.z_setpoint = DESIRED_DEPTH
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = self.start_yaw
        
        msg.z_measurement = context['depth']
        msg.roll_measurement = context['odom']['roll']
        msg.pitch_measurement = context['odom']['pitch']
        msg.yaw_measurement = context['odom']['yaw']
        
        context['pid_publisher'].publish(msg)
        
        return None # technically not needed since returning nothing is returning None
        
        
        