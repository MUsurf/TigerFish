from datetime import datetime

from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import String

from remote_controller.app import \
    make_http_str_post, \
    make_http_controller_input_post

from messages.msg import ControllerInput

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

        ## defunct without setpointobj or message to send
        ## needs proper msg formatting
        # self.curr_position = SomeSetpointObj()
        # self.curr_velocity = SomeSetpointObj()

        # # datetime(1970,1,1) represents never set
        # self.curr_position_last_set = datetime(1970,1,1)
        # self.curr_velocity_last_set = datetime(1970,1,1)

        self.controller_input = ControllerInput()
        self.controller_input_last_set = datetime(1970,1,1)

        self.get_endpoints = {
            ## can't function without working setpoi
            # "curr_position": make_http_imu_get(
            #     lambda: self.curr_position,
            #     lambda: self.curr_position_last_set
            # ),
            # "curr_velocity": make_http_imu_get(
            #     lambda: self.curr_velocity,
            #     lambda: self.curr_velocity_last_set
            # )
        }

        self.post_endpoints = {
            "controller_input": make_http_controller_input_post(
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
            ControllerInput,
            "controller_input",
            QOS
        )

        self.timer = self.create_timer(1.0 / FREQUENCY, self.timer_callback)

    def timer_callback(self):

        # publish topics
        self.controller_input_publisher.publish(
            self.controller_input
        )



    def publish_command_line(self, msg: str):
        
        ros2_msg = String()
        ros2_msg.data = msg
        self.command_publisher.publish(ros2_msg)

        

    # def update_curr_position(self, msg: SomeSetpointObj):
    #     self.get_logger().info(f"updated curr_position to: {msg}")
    #     self.curr_position = msg
    #     self.curr_position_last_set = datetime.now()

    # def update_curr_velocity(self, msg: SomeSetpointObj):
    #     self.get_logger().info(f"updated curr_velocity to: {msg}")
    #     self.curr_velocity = msg
    #     self.curr_velocity_last_set = datetime.now()

    def update_controller_input(self, msg: dict):
        self.controller_input_last_set = datetime.now()
        # self.get_logger().info(
        #     f"updated controller_input at {self.controller_input_last_set}"
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