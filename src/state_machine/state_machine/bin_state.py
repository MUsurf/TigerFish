from abc import ABC, abstractmethod
import math
from messages.msg import PIDInput, VisionMessage

class FindBins(ABC):
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
        msg.x_mode = False
        msg.x_power = 0.3
        msg.y_mode = True
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

        if camera_see_bins_any:
            return FindRoleBin
        
class FindRoleBin(ABC):
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
        msg.x_mode = False
        msg.x_power = 0.05
        msg.y_mode = True
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

        if camera_see_role_bin:
            return OverRoleBin
        
class OverRoleBin(ABC):
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
        msg.x_setpoint = bucket_with_correct_photo_x_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
        msg.y_mode = True
        msg.x_setpoint = bucket_with_correct_photo_y_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
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
        
        if math.abs(bucket_with_correct_photo_x_offset) < 5 and math.abs(bucket_with_correct_photo_y_offset) < 5:
            return next_state
        
class DropThings(ABC):
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
        msg.x_setpoint = bucket_with_correct_photo_x_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
        msg.y_mode = True
        msg.x_setpoint = bucket_with_correct_photo_y_offset * 0.2 # TODO - hemmy, uhhh, this camera bottom, the .2 is so it dont go too fast
        msg.measurement_x = 0.0
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
        
        drop thing 1

        prob sleep

        drop thing 2

        next state