from state_machine.state import State
from messages.msg import PIDInput
import time

class GateSetRoleState(State):
    def __init__(self):
        super().__init__('gate_set_role')
        
        self.start_yaw : float | None = None
        self.desired_depth : float | None = None
        
    def start(self, context : dict):
        self.start_yaw = 0.0
        self.desired_depth = context['gate_state_depth']
        return None
        
    def execute(self, context : dict):
        survey_and_repair = context['survey_and_repair_gate_image_left_gate']
        search_and_rescue = context['search_and_rescue_gate_image_left_gate']
        if survey_and_repair.is_detected and search_and_rescue.is_detected:
            context['role'] = 'survey_and_repair' if abs(survey_and_repair.x_position) < abs(search_and_rescue.x_position) else 'search_and_rescue'
            return 'go_through_gate'
        
        msg = PIDInput()
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
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
        
        
        