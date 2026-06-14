import math

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput
from std_msgs.msg import Float32

from yasmin import State, StateMachine, Blackboard
from yasmin_viewer import YasminViewerPub
from context import Context

import numpy as np

# All states
import state_machine.init_states as init_states
from init_states.init_states import STATE_GETTERS as INIT_STATE_GETTERS
import state_machine.gate_states as gate_states
from gate_states.gate_states import STATE_GETTERS as GATE_STATE_GETTERS
import state_machine.slalom_states as slalom_states
from slalom_states.slalom_states import STATE_GETTERS as SLALOM_STATE_GETTERS
import state_machine.bins_states as bins_states
from bins_states.bins_states import STATE_GETTERS as BINS_STATE_GETTERS
import state_machine.octagon_states as octagon_states
from octagon_states.octagon_states import STATE_GETTERS as OCTAGON_STATE_GETTERS
# Prob won't use
from state_machine.torpedo_states import *

def rpy_from_quat(q):
    """
    Convert geometry_msgs.msg.Quaternion to roll, pitch, yaw (radians).

    Assumes quaternion fields:
        q.x, q.y, q.z, q.w
    Uses XYZ (roll, pitch, yaw) convention.
    """

    x = q.x
    y = q.y
    z = q.z
    w = q.w

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
        
        self.orientation_subscriber = self.create_subscription( # IMU?
            Odometry, "state_estimation", self._odom_cb, 10
        )
        
        self.depth_sensor_subscriber = self.create_subscription(
            Float32, "depth", self.depth_sensor_cb, 10
        )
                
        # ADD ALL VISION SUBSCRIBERS HERE
        
        # -----
        
        self.pid_publisher = self.create_publisher(PIDInput, "pid_input", 10)
        
        # ADD ALL VISION PUBLISHERS HERE
        
        self.context = Context(
            self, 
            self.pid_publisher,
            # VISION PUBLISHERS * NOT SUBSCRIBERS
        )

        # Create state machine
        self.state_machine = StateMachine(outcomes={"complete"})
        
        
        # This is for ease of individual development
        state_getter_lists = [
            INIT_STATE_GETTERS,
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
        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        
        orientation_list = [qx, qy, qz, qw]
        roll, pitch, yaw = rpy_from_quat(orientation_list)
        
        self.blackboard["odom"] = { # Do we need more than rpy?
            "roll" : roll,
            "pitch" : pitch,
            "yaw" : yaw             
        }

    def depth_sensor_cb(self, msg):
        self.blackboard["depth"] = msg.data
        
        
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
