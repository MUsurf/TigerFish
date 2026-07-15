import math
from state_machine.state import State
from messages.msg import PIDInput, VisionMessage

class OctagonTurn(State):
    def __init__(self, name):
        self.name = name
        self.start_yaw = 0
        
    def start(self, context : dict) -> None:
        self.start_yaw = context["odom"]["yaw"]
        return None
        
    def execute(self, context : dict) -> str | None:

        msg = PIDInput()
        odom = context["odom"]
        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.z_setpoint = 1.0
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

        if math.abs(odom["yaw"] - (self.start_yaw - 90)) < 5:
            return "octagon_go_to"
        
class OctagonGoTo(State):
    def __init__(self, name):
        self.name = name
        self.start_yaw = 0
        
    def start(self, context : dict) -> None:
        self.start_yaw = context["odom"]["yaw"]
        return None
        
    def execute(self, context : dict) -> str | None:

        msg = PIDInput()
        odom = context["odom"]
        msg.x_mode = False
        msg.x_power = 0.2
        msg.y_mode = True
        msg.z_mode = True
        msg.z_setpoint = 1.0
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
            return "octagon_send_it"  #TODO - note, we are at 1m, and we send it as soon as we see the table, will this be too soon?

class OctagonSendIt(State):
    def __init__(self, name):
        self.name = name
        self.start_yaw = 0
        
    def start(self, context : dict) -> None:
        self.start_yaw = context["odom"]["yaw"]
        return None
        
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