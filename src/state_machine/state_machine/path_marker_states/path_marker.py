import time
import yasmin
import math
from yasmin import State, Blackboard
from messages.msg import PIDInput, VisionMessage

class PathMarkerState(State):
    def __init__(self):
        super().__init__(outcomes=["next_task"])

    def execute(self, blackboard: Blackboard):

        # # If no path marker, do a little slip around seatch
        # while not marker:
        #     msg = PIDInput()
        #     odom = blackboard.get("odom")
        #     msg.x_mode = True
        #     msg.y_mode = True
        #     msg.z_mode = True
        #     msg.roll_mode = True
        #     msg.pitch_mode = True
        #     msg.yaw_mode = False
        #     msg.pitch_setpoint = 0.0
        #     msg.measurement_pitch = odom["pitch"]
        #     msg.roll_setpoint = 0.0
        #     msg.measurement_roll = odom["roll"]
        #     msg.yaw_power = 0.05
        #     self.context.pid_publisher.publish(msg)
        #     time.sleep(0.05)

        # Once see get angle to, align yaw
        msg = PIDInput()
        odom = blackboard.get("odom")
        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        msg.yaw_setpoint = henry_given_angle + odom["yaw"]
        msg.measurement_yaw = odom["yaw"]
        self.context.pid_publisher.publish(msg)
        
        while math.abs(odom["yaw"] - henry_given_angle) > 1:
            time.sleep(0.05)

        stored_yaw = odom["yaw"]

        # inch forwarad
        while not bottom_camera_see:
            msg = PIDInput()
            odom = blackboard.get("odom")
            msg.x_mode = False
            msg.x_power = 0.05
            msg.y_mode = True
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = True
            msg.pitch_setpoint = 0.0
            msg.measurement_pitch = odom["pitch"]
            msg.roll_setpoint = 0.0
            msg.measurement_roll = odom["roll"]
            msg.yaw_setpoint = henry_given_angle + odom["yaw"]
            msg.measurement_yaw = odom["yaw"]
            self.context.pid_publisher.publish(msg)
            time.sleep(0.05)

        # center on bottom camera
        while distance_from_x_center > 1 or distance_from_y_center > 1:
            msg = PIDInput()
            odom = blackboard.get("odom")
            msg.x_mode = True
            msg.x_setpoint = distance_from_x_center
            msg.x_measurement = 0.0
            msg.y_mode = True
            msg.y_setpoint = distance_from_y_center
            msg.y_measurement = 0.0
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = True
            msg.pitch_setpoint = 0.0
            msg.measurement_pitch = odom["pitch"]
            msg.roll_setpoint = 0.0
            msg.measurement_roll = odom["roll"]
            msg.yaw_setpoint = stored_yaw
            msg.measurement_yaw = odom["yaw"]
            self.context.pid_publisher.publish(msg)
            time.sleep(0.05)

        # spin to match it
        msg = PIDInput()
        odom = blackboard.get("odom")
        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]
        msg.yaw_setpoint = henry_marker_angle + odom["yaw"]
        msg.measurement_yaw = odom["yaw"]
        self.context.pid_publisher.publish(msg)

        while math.abs(odom["yaw"] - henry_marker_angle) > 1:
            time.sleep(0.05)

        # done boss

        return "next_task"

# TODO - is the below finction needed?
# def get_slalom_state(context):
#     state = SlalomState()
#     transitions = {
#     # ODO - fix this transition and like evreything else frfr
#         "next_task": "NEXT_STATE_NAME",
#         "done": "complete",
#     }
#     return "SLALOM", state, transitions

# General Idea:
#
# Find the 