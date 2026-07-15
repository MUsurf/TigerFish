from abc import ABC, abstractmethod
import math
from messages.msg import PIDInput, VisionMessage

class OctagonTurn(ABC):
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
        msg.yaw_setpoint = -50.0
        msg.measurement_yaw = odom["yaw"]
        self.context.pid_publisher.publish(msg)

        if math.abs(odom["yaw"] - (-50.0)) < 5:
            return OctagonGoTo
        
class OctagonGoTo(ABC):
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
        msg.x_power = 0.2
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
        msg.yaw_setpoint = self.start_yaw - 90
        msg.measurement_yaw = odom["yaw"]
        self.context.pid_publisher.publish(msg)

        if see_table:
            return OctagonSendIt  #TODO - note, we are at 1m, and we send it as soon as we see the table, will this be too soon?

class OctagonSendIt(ABC):
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
        msg.y_mode = True
        msg.z_mode = False
        msg.z_power = 0.6
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        self.context.pid_publisher.publish(msg)