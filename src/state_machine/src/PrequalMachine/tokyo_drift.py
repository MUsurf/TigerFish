import time

import rclpy

import yasmin
from yasmin import State, Blackboard
from messages.msg import PIDInput
from context import Context

class TokyoDrift(State):
    """
    Move around pole
    """
    def __init__(self, context: Context) -> None:
        """
        Move around pole

        Outcomes:
            next_state: Go back to gate alignment
        """
        super().__init__(["next_state"])
        self.context = context
        self.set_description(
            "Move around pole"
        )
        self.strafe_power = 0.4
        self.initial_yaw = None
        self.last_yaw = None
        self.unwrapped_yaw = None
        self.heading_tolerance = 5.0
        self.min_rotation = 360.0

    def execute(self, blackboard: Blackboard):
        """
        Executes the logic for the state.

        Args:

        Returns:

        Raises:
            Exception: May raise exceptions related to state execution.
        """
        yasmin.YASMIN_LOG_INFO("Executing state TOKYO_DRIFT")
        pole = blackboard.get("pole_detection")
        odom = blackboard.get("odom")
        depth = blackboard.get("depth")
        desired_depth = self.context.desired_depth

        if odom is None or depth is None:
            return

        current_yaw = odom["yaw"]

        if self.initial_yaw is None:
            self.initial_yaw = current_yaw
            self.last_yaw = current_yaw
            self.unwrapped_yaw = current_yaw

        delta = current_yaw - self.last_yaw
        if delta > 180.0:
            delta -= 360.0
        elif delta < -180.0:
            delta += 360.0
        self.unwrapped_yaw += delta
        self.last_yaw = current_yaw

        msg = PIDInput()

        msg.z_mode = True
        msg.z_measurement = depth
        msg.z_setpoint = desired_depth

        msg.yaw_mode = True
        msg.yaw_measurement = current_yaw

        if pole and pole.get("seen"):
            yaw_error = pole.get("yaw_angle", 0.0)
            msg.yaw_setpoint = current_yaw + yaw_error
            msg.y_power = self.strafe_power
        else:
            msg.yaw_setpoint = current_yaw
            msg.y_power = 0.0

        self.context.pid_publisher.publish(msg)

        total_rotation = self.unwrapped_yaw - self.initial_yaw
        angle_diff = (current_yaw - self.initial_yaw + 180.0) % 360.0 - 180.0

        if abs(total_rotation) >= self.min_rotation and abs(angle_diff) <= self.heading_tolerance:
            self.initial_yaw = None
            self.last_yaw = None
            self.unwrapped_yaw = None
            return "next_state"