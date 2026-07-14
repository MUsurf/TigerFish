from abc import ABC, abstractmethod
import math
from messages.msg import PIDInput, VisionMessage
from bin_state import FindBins

# TODO - henry, just conform to what it do for real for real, cause uhh... its like the best for me
        
class PathMarkerSee(ABC):
    def __init__(self, name):
        self.name = name
        self.start_yaw = 0
        
    @abstractmethod
    def start(self, context : dict) -> None:
        self.start_yaw = context["odom"]["yaw"]
        return None
    
    @abstractmethod
    def execute(self, context : dict) -> str | None:

        msg = PIDInput()
        odom = context["odom"]
        msg.x_mode = True
        msg.x_setpoint = marker_x_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
        msg.y_mode = True
        msg.y_setpoint = marker_y_offset * 0.2
        msg.measurement_y = 0.0
        msg.z_mode = True
        msg.z_setpoint = 1
        msg.z_measurement = context['depth']
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        msg.yaw_setpoint = self.start_yaw
        msg.measurement_yaw = odom["yaw"]
        self.context.pid_publisher.publish(msg)

        if math.abs(marker_x_offset) < 5 and math.abs(marker_y_offset) < 5:
            return PathMarkerSpin
        
class PathMarkerSpin(ABC):
    def __init__(self, name):
        self.name = name
        
    @abstractmethod
    def start(self, context : dict) -> None:
        return None
        
    @abstractmethod
    def execute(self, context : dict) -> str | None:

        msg = PIDInput()
        odom = context["odom"]
        msg.x_mode = True
        msg.x_setpoint = marker_x_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
        msg.y_mode = True
        msg.y_setpoint = marker_y_offset * 0.2
        msg.measurement_y = 0.0
        msg.z_mode = True
        msg.z_setpoint = 1
        msg.z_measurement = context['depth']
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        msg.yaw_setpoint = 0.0
        msg.measurement_yaw = yaw_angle_to_marker # TODO same thing as before but bottom NOTEE - this requires that you givr me the right direction, if not very bad
        self.context.pid_publisher.publish(msg)

        if math.abs(yaw_angle_to_marker) < 5:
            return FindBins