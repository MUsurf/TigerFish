from datetime import datetime

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String
from nav_msgs.msg import Odometry

from remote_controller.app import (
    make_http_rpy_get,
    make_http_gui_box_get,
    make_http_str_post,
    make_http_controller_input_post,
)
from messages.msg import ControllerInput, GuiBox

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)
FREQUENCY = 40
NUM_GUI_BOXES = 6

class RemoteControllerNode(Node):
    def __init__(self):
        super().__init__("main")

        # --- node's internally kept values ---

        self.odometry = Odometry()
        self.odometry_stamp = datetime(1970, 1, 1)

        self.controller_input = ControllerInput()
        self.controller_input_stamp = datetime(1970, 1, 1)

        self.get_endpoints = {
            "get_boxes": make_http_gui_box_get(
                lambda: self.gui_boxes
            ),
            "get_odometry": make_http_rpy_get(
                lambda: self.odometry, lambda: self.odometry_stamp
            )
        }

        self.post_endpoints = {
            "controller_input": make_http_controller_input_post(
                self.update_controller_input
            ),
            "command_line": make_http_str_post(self.publish_command_line),
        }

        self.gui_boxes: list[GuiBox] = []
        self.gui_box_subscribers = []
        for i in range(NUM_GUI_BOXES):
            curr_box = GuiBox()
            curr_box.id = i
            self.gui_boxes.append(curr_box)

        self.orientation_subscriber = self.create_subscription(
            Odometry, "state_estimation", self._odom_cb, QOS
        )
        self.gui_box_subscriber = self.create_subscription(
            GuiBox, "gui_box", self._gui_box_cb, QOS
        )

        self.command_publisher = self.create_publisher(String, "command_line", QOS)
        self.controller_input_publisher = self.create_publisher(
            ControllerInput, "controller_input", QOS
        )

        self.timer = self.create_timer(1.0 / FREQUENCY, self._timer_callback)

    def _timer_callback(self):

        # publish topics
        self.controller_input_publisher.publish(self.controller_input)

    def _odom_cb(self, msg: Odometry):
        self.odometry = msg

    def _gui_box_cb(self, msg: GuiBox):
        if msg.id < 0 or NUM_GUI_BOXES <= msg.id:
            return

        self.gui_boxes[msg.id] = msg

    def publish_command_line(self, cmd: str):

        msg = String()
        msg.data = cmd
        self.command_publisher.publish(msg)

    def update_controller_input(self, msg: dict):
        self.controller_input_stamp = datetime.now()
        # self.get_logger().info(
        #     f"updated controller_input at {self.controller_input_stamp}"
        # )

        self.controller_input.x_left_stick = msg["x_left_stick"]
        self.controller_input.y_left_stick = msg["y_left_stick"]
        self.controller_input.x_right_stick = msg["x_right_stick"]
        self.controller_input.y_right_stick = msg["y_right_stick"]

        self.controller_input.a_button = msg["a_button"]
        self.controller_input.b_button = msg["b_button"]
        self.controller_input.x_button = msg["x_button"]
        self.controller_input.y_button = msg["y_button"]

        self.controller_input.up_dpad = msg["up_dpad"]
        self.controller_input.right_dpad = msg["right_dpad"]
        self.controller_input.down_dpad = msg["down_dpad"]
        self.controller_input.left_dpad = msg["left_dpad"]

        self.controller_input.r_bumper = msg["r_bumper"]
        self.controller_input.l_bumper = msg["l_bumper"]
        self.controller_input.r_trigger = msg["r_trigger"]
        self.controller_input.l_trigger = msg["l_trigger"]