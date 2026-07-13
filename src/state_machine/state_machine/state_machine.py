import math

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput, VisionMessage
from std_msgs.msg import Float32

from state_machine.state_machine.state import State

from state_machine.state_machine.start_state import StartState
from state_machine.state_machine.gate_go_to_depth import GateGoToDepthState
from state_machine.state_machine.gate_set_role import GateSetRoleState
from state_machine.state_machine.go_through_gate import GoThroughGateState

from state_machine.state_machine.end_state import EndState


import numpy as np

def roll_pitch_yaw_from_quaternion(quaternion):
    """
    Convert geometry_msgs.msg.Quaternion to roll, pitch, yaw (radians).

    Assumes quaternion fields:
        quaternion.x, quaternion.y, quaternion.z, quaternion.w
    Uses XYZ (roll, pitch, yaw) convention.
    """

    x = quaternion.x
    y = quaternion.y
    z = quaternion.z
    w = quaternion.w

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.sign(sinp) * (np.pi / 2.0)  # use 90° if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


class StateMachineNode(Node): 
    def __init__(self):
        super().__init__("state_machine_node")
        
        self.context = {}
        
        # configs
        self.context["start_depth_threshold"] = 0.03 # meters
        self.context["start_time"] = 3.0 # seconds
        self.context["gate_state_depth"] = 1.0 # meters
        self.context["depth_error_tolerance"] = 0.075 # meters
        self.context["time_in_depth_requirement"] = 10.0 # seconds
        self.context["gate_forward_time"] = 10.0 # seconds
        self.context["gate_forward_power"] = 0.5 # power
        
        self.context["slalom_shift_time"] = 6.0 # seconds
        self.context["slalom_shift_power"] = 0.5 # power
        self.context["slalom_shift_direction"] = -1.0 # direction, -1 for left and 1 for right
        self.context["do_shift"] = True
        
        self.context["slalom_forward_time"] = 15.0 # seconds
        self.context["slalom_forward_power"] = 0.5
    
        # context defaults:
        self.context["survey_and_repair_gate_image_left_gate"] = VisionMessage()
        self.context["survey_and_repair_gate_image_right_gate"] = VisionMessage()
        self.context["search_and_rescue_gate_image_left_gate"] = VisionMessage()
        self.context["search_and_rescue_gate_image_right_gate"] = VisionMessage()
        self.context["survey_and_repair_gate_image_left_bin"] = VisionMessage()
        self.context["survey_and_repair_gate_image_right_bin"] = VisionMessage()
        self.context["search_and_rescue_gate_image_left_bin"] = VisionMessage()
        self.context["search_and_rescue_gate_image_right_bin"] = VisionMessage()
        self.context["octagon_image_1_left"] = VisionMessage()
        self.context["octagon_image_1_right"] = VisionMessage()
        self.context["octagon_image_2_left"] = VisionMessage()
        self.context["octagon_image_2_right"] = VisionMessage()
        self.context["table_left"] = VisionMessage()
        self.context["table_right"] = VisionMessage()


        self.context["odom"] = {"roll" : 0.0, "pitch" : 0.0, "yaw" : 0.0}
        self.context["depth"] = -1.0
        
        
        # Subscriptions
        self.orientation_subscriber = self.create_subscription(
            Odometry, "state_estimation", self._odom_cb, 10)
        self.depth_sensor_subscriber = self.create_subscription(
            Float32, "depth", self.depth_sensor_cb, 10)
        self.survey_and_repair_gate_left_gate_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_left_gate", self.survey_and_repair_gate_image_left_gate_cb, 10)
        self.survey_and_repair_gate_right_gate_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_right_gate", self.survey_and_repair_gate_image_right_gate_cb, 10)
        self.search_and_rescue_gate_left_gate_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_left_gate", self.search_and_rescue_gate_image_left_gate_cb, 10)
        self.search_and_rescue_gate_right_gate_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_right_gate", self.search_and_rescue_gate_image_right_gate_cb, 10)
        self.survey_and_repair_gate_left_bin_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_left_bin", self.survey_and_repair_gate_image_left_bin_cb, 10)
        self.survey_and_repair_gate_right_bin_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_right_bin", self.survey_and_repair_gate_image_right_bin_cb, 10)
        self.search_and_rescue_gate_left_bin_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_left_bin", self.search_and_rescue_gate_image_left_bin_cb, 10)
        self.search_and_rescue_gate_right_bin_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_right_bin", self.search_and_rescue_gate_image_right_bin_cb, 10)
        self.octagon_image_1_left_subscriber = self.create_subscription(
            VisionMessage, "octagon_image_1_left", self.octagon_image_1_left_cb, 10)
        self.octagon_image_1_right_subscriber = self.create_subscription(
            VisionMessage, "octagon_image_1_right", self.octagon_image_1_right_cb, 10)
        self.octagon_image_2_left_subscriber = self.create_subscription(
            VisionMessage, "octagon_image_2_left", self.octagon_image_2_left_cb, 10)
        self.octagon_image_2_right_subscriber = self.create_subscription(
            VisionMessage, "octagon_image_2_right", self.octagon_image_2_right_cb, 10)
        self.table_left_subscriber = self.create_subscription(
            VisionMessage, "table_left", self.table_left_cb, 10)
        self.table_right_subscriber = self.create_subscription(
            VisionMessage, "table_right", self.table_right_cb, 10)

        # Publishers
        self.pid_publisher = self.create_publisher(
            PIDInput, "pid_input", 10)

        self.context['pid_publisher'] = self.pid_publisher
        
        self.states = {
            'start' : StartState(),
            'gate_go_to_depth' : GateGoToDepthState(),
            'gate_set_role': GateSetRoleState(),
            'go_through_gate' : GoThroughGateState(),
            
            'end' : EndState(),
        }
        
        self.current_state : State = self.states['start']
        
        self.timer = self.create_timer(0.05, self.timer_cb)
        self.get_logger().info("State machine initialized successfully!")
        
    def timer_cb(self):
        next_state : State | None = self.current_state.execute(self.context)
        if next_state is not None:
            self.current_state = self.states[next_state]
            self.current_state.start(self.context)
        
        self.get_logger().info(f'Current state: {self.current_state.name}')
        
    def _odom_cb(self, msg):
        roll, pitch, yaw = roll_pitch_yaw_from_quaternion(msg.pose.pose.orientation)

        self.context["odom"] = { # Do we need more than roll, pitch, yaw?
            "roll" : roll,
            "pitch" : pitch,
            "yaw" : yaw             
        }
    def depth_sensor_cb(self, msg):
        self.context["depth"] = msg.data
    def survey_and_repair_gate_image_left_gate_cb(self, msg):
        self.context["survey_and_repair_gate_image_left_gate"] = msg
    def survey_and_repair_gate_image_right_gate_cb(self, msg):
        self.context["survey_and_repair_gate_image_right_gate"] = msg
    def search_and_rescue_gate_image_left_gate_cb(self, msg):
        self.context["search_and_rescue_gate_image_left_gate"] = msg
    def search_and_rescue_gate_image_right_gate_cb(self, msg):
        self.context["search_and_rescue_gate_image_right_gate"] = msg
    def survey_and_repair_gate_image_left_bin_cb(self, msg):
        self.context["survey_and_repair_gate_image_left_bin"] = msg
    def survey_and_repair_gate_image_right_bin_cb(self, msg):
        self.context["survey_and_repair_gate_image_right_bin"] = msg
    def search_and_rescue_gate_image_left_bin_cb(self, msg):
        self.context["search_and_rescue_gate_image_left_bin"] = msg
    def search_and_rescue_gate_image_right_bin_cb(self, msg):
        self.context["search_and_rescue_gate_image_right_bin"] = msg
    def octagon_image_1_left_cb(self, msg):
        self.context["octagon_image_1_left"] = msg
    def octagon_image_1_right_cb(self, msg):
        self.context["octagon_image_1_right"] = msg
    def octagon_image_2_left_cb(self, msg):
        self.context["octagon_image_2_left"] = msg
    def octagon_image_2_right_cb(self, msg):
        self.context["octagon_image_2_right"] = msg 
    def table_left_cb(self, msg):
        self.context["table_left"] = msg
    def table_right_cb(self, msg):
        self.context["table_right"] = msg 
    
        
        
def main(args=None):
    rclpy.init(args=args)
    node = StateMachineNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
