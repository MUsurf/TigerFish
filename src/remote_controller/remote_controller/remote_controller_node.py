from datetime import datetime

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from remote_controller.ControllerValues import ControllerValues
from remote_controller.app import \
    make_http_str_get, make_http_str_post, \
    make_http_imu_get, make_http_imu_post

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)
FREQUENCY = 40
LEGAL_MODES = [
    "idle",
    "target_velocity",
    "target_position",
]

class RemoteControllerNode(Node):
    def __init__(self):
        super().__init__('main')

        # --- node's internally kept values ---
        self.curr_position = ControllerValues()
        self.curr_velocity = ControllerValues()

        # datetime(1970,1,1) represents never set
        self.curr_position_last_set = datetime(1970,1,1)
        self.curr_velocity_last_set = datetime(1970,1,1)

        self.controller_input = String()
        self.controller_input.data = ""
        self.controller_input_last_set = datetime(1970,1,1)

        self.get_endpoints = {
            "curr_position": make_http_imu_get(
                lambda: self.curr_position,
                lambda: self.curr_position_last_set
            ),
            "curr_velocity": make_http_imu_get(
                lambda: self.curr_velocity,
                lambda: self.curr_velocity_last_set
            )
        }

        self.post_endpoints = {
            "controller_input": make_http_str_post(
                self.update_controller_input
            ),
            "command_line": make_http_str_post(
                self.publish_command_line
            )
        }

        self.command_publisher = self.create_publisher(
            String,
            "command_line",
            QOS
        )
        self.controller_input_publisher = self.create_publisher(
            String,
            "controller_input",
            QOS
        )

        self.timer = self.create_timer(1.0 / FREQUENCY, self.timer_callback)

    def timer_callback(self):

        # publish topics
        self.controller_input_publisher.publish(
            self.controller_input
        )
        

    def update_curr_position(self, msg: ControllerValues):
        self.get_logger().info(f"updated curr_position to: {msg}")
        self.curr_position = msg
        self.curr_position_last_set = datetime.now()

    def update_curr_velocity(self, msg: ControllerValues):
        self.get_logger().info(f"updated curr_velocity to: {msg}")
        self.curr_velocity = msg
        self.curr_velocity_last_set = datetime.now()

    def update_controller_input(self, msg: str):
        self.get_logger().info(f"updated controller_input to: {msg}")
        self.controller_input.data = msg
        self.controller_input_last_set = datetime.now()

    def publish_command_line(self, msg: str):
        
        ros2_msg = String()
        ros2_msg.data = msg
        self.command_publisher.publish(ros2_msg)