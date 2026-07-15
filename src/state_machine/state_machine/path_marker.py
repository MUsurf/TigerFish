import math
from state_machine.state import State
from messages.msg import PIDInput, VisionMessage
import time
        
class CenterOnPathMarker(State):
    def __init__(self):
        super().__init__('center_on_path_marker')
        self.start_yaw = 0.0
        self.start_time = None
        
    def start(self, context : dict) -> None:
        self.start_yaw = context["odom"]["yaw"]
        self.start_time = None
        return None
    
    def execute(self, context : dict) -> str | None:
        if not context["path_marker_left"].is_detected:
            msg = PIDInput()
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = True
            
            msg.z_setpoint = 1.0
            msg.roll_setpoint = 0.0
            msg.pitch_setpoint = 0.0
            msg.yaw_setpoint = self.start_yaw
            
            msg.z_measurement = context['depth']
            msg.roll_measurement = context["odom"]["roll"]
            msg.pitch_measurement = context["odom"]["pitch"]
            msg.yaw_measurement = context["odom"]["yaw"]
            
            self.context.pid_publisher.publish(msg)
            
            return None
        x_pos = context["path_marker_left"].y_position
        y_pos = context["path_marker_left"].x_position
        
        msg = PIDInput()
        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.x_setpoint = x_pos
        msg.y_setpoint = y_pos
        msg.z_setpoint = 1.0
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = self.start_yaw
        
        msg.x_measurement = 0.0
        msg.y_measurement = 0.0
        msg.z_measurement = context['depth']
        msg.roll_measurement = context["odom"]["roll"]
        msg.pitch_measurement = context["odom"]["pitch"]
        msg.yaw_measurement = context["odom"]["yaw"]
        
        self.context.pid_publisher.publish(msg)

        if math.abs(x_pos) < context['path_marker_align_distance_threshold'] and math.abs(y_pos) < context['path_marker_align_distance_threshold']:
            if self.start_time is None:
                self.start_time = time.time()
            elif time.time() - self.start_time >= context['path_marker_align_distance_time']: 
                return 'path_marker_spin'
        else:
            self.start_time = None
        
class PathMarkerSpin(State):
    def __init__(self):
        super().__init__('path_marker_spin')
        self.path_marker_align_distance_threshold = None
        self.path_marker_heading = None
        self.align_time = None
        self.start_time = None
        
    def start(self, context : dict) -> None:
        self.path_marker_align_distance_threshold = context["path_marker_align_distance_threshold"]
        self.path_marker_heading = context["path_marker_heading"]
        self.align_time = context["path_marker_align_heading_time"]
        self.start_time = None
        return None
        
    def execute(self, context : dict) -> str | None:
        x_pos = context["path_marker_left"].y_position
        y_pos = context["path_marker_left"].x_position
        
        msg = PIDInput()
        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.x_setpoint = x_pos
        msg.y_setpoint = y_pos
        msg.z_setpoint = 1.0
        msg.roll_setpoint = 0.0
        msg.pitch_setpoint = 0.0
        msg.yaw_setpoint = self.path_marker_heading
        
        msg.x_measurement = 0.0
        msg.y_measurement = 0.0
        msg.z_measurement = context['depth']
        msg.roll_measurement = context["odom"]["roll"]
        msg.pitch_measurement = context["odom"]["pitch"]
        msg.yaw_measurement = context["odom"]["yaw"]
        
        self.context.pid_publisher.publish(msg)

        if math.abs(x_pos) < self.path_marker_align_distance_threshold and math.abs(y_pos) < self.path_marker_align_distance_threshold:
            if self.start_time is None:
                self.start_time = time.time()
            elif time.time() - self.start_time >= self.align_time: 
                return '...'
        else:
            self.start_time = None