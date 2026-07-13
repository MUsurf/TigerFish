import math

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput, VisionMessage
from std_msgs.msg import Float32

from yasmin import State, StateMachine, Blackboard
from yasmin_viewer import YasminViewerPub

import numpy as np

# All states
import state_machine.start_states as init_states
from start_states.start_states import STATE_GETTERS as START_STATE_GETTERS
import state_machine.gate_states as gate_states
from gate_states.gate_states import STATE_GETTERS as GATE_STATE_GETTERS
import state_machine.slalom_states as slalom_states

from TigerFish.src.state_machine.state_machine.slalom_states.slalom_states import STATE_GETTERS as SLALOM_STATE_GETTERS
import state_machine.bins_states as bins_states
from bins_states.bins_states import STATE_GETTERS as BINS_STATE_GETTERS
import state_machine.octagon_states as octagon_states
from octagon_states.octagon_states import STATE_GETTERS as OCTAGON_STATE_GETTERS
# Prob won't use
from state_machine.torpedo_states import *

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
        
        self.blackboard = Blackboard()
        # blackboard defaults:
        self.blackboard["survey_and_repair_gate_image_left"] = VisionMessage()
        self.blackboard["survey_and_repair_gate_image_right"] = VisionMessage()
        self.blackboard["search_and_rescue_gate_image_left"] = VisionMessage()
        self.blackboard["search_and_rescue_gate_image_right"] = VisionMessage()
        self.blackboard["odom"] = {"roll" : 0.0, "pitch" : 0.0, "yaw" : 0.0}
        self.blackboard["depth"] = -1.0
        
        
        self.orientation_subscriber = self.create_subscription(Odometry, "state_estimation", self._odom_cb, 10)
        self.depth_sensor_subscriber = self.create_subscription(Float32, "depth", self.depth_sensor_cb, 10)
        self.survey_and_repair_gate_image_left_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_left", self.survey_and_repair_gate_image_left_cb, 10
        )
        self.survey_and_repair_gate_image_right_subscriber = self.create_subscription(
            VisionMessage, "survey_and_repair_gate_image_right", self.survey_and_repair_gate_image_right_cb, 10
        )
        self.search_and_rescue_gate_image_left_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_left", self.search_and_rescue_gate_image_left_cb, 10
        )
        self.search_and_rescue_gate_image_right_subscriber = self.create_subscription(
            VisionMessage, "search_and_rescue_gate_image_right", self.search_and_rescue_gate_image_right_cb, 10
        )

        self.pid_publisher = self.create_publisher(PIDInput, "pid_input", 10)
        
        self.context = dict({
            "pid_publisher" : self.pid_publisher,
        })

        # Create state machine
        self.state_machine = StateMachine(outcomes={"complete"})
        
        
        # This is for ease of individual development
        state_getter_lists = [
            START_STATE_GETTERS,
            GATE_STATE_GETTERS,
            SLALOM_STATE_GETTERS,
            BINS_STATE_GETTERS,
            OCTAGON_STATE_GETTERS
        ]
        for state_getter_list in state_getter_lists:
            for state_getter in state_getter_list:
                name, state, transitions = state_getter(self.context)
                self.state_machine.add_state(name, state, transitions)

        # Set up state machine
        self.state_machine.set_start_state("...?") # Whatever we put in init_states
    
        self.timer = self.create_timer(0.05, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")
        
        
    
    # Call back functions keep blackboard up to date with ROS topics

    def _odom_cb(self, msg):
        quaternion_x = msg.pose.pose.orientation.x
        quaternion_y = msg.pose.pose.orientation.y
        quaternion_z = msg.pose.pose.orientation.z
        quaternion_w = msg.pose.pose.orientation.w

        orientation_list = [quaternion_x, quaternion_y, quaternion_z, quaternion_w]
        roll, pitch, yaw = roll_pitch_yaw_from_quaternion(orientation_list)

        self.blackboard["odom"] = { # Do we need more than roll, pitch, yaw?
            "roll" : roll,
            "pitch" : pitch,
            "yaw" : yaw             
        }
    def depth_sensor_cb(self, msg):
        self.blackboard["depth"] = msg.data
    def survey_and_repair_gate_image_left_cb(self, msg):
        self.blackboard["survey_and_repair_gate_image_left"] = msg
    def survey_and_repair_gate_image_right_cb(self, msg):
        self.blackboard["survey_and_repair_gate_image_right"] = msg
    def search_and_rescue_gate_image_left_cb(self, msg):
        self.blackboard["search_and_rescue_gate_image_left"] = msg
    def search_and_rescue_gate_image_right_cb(self, msg):
        self.blackboard["search_and_rescue_gate_image_right"] = msg
        
        
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
