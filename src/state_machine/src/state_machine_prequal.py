import time

import rclpy
from rclpy.node import Node

from yasmin.state import State
from yasmin.state_machine import StateMachine
from yasmin_viewer.yasmin_viewer_pub import YasminViewerPub

from messages.msg import PIDInput
from messages.msg import depth


class StartingState(State):
    def __init__(self):
        # valid outcomes for this state
        super().__init__(outcomes=["finished"])

    def execute(self) -> str:
        msg = PIDInput()
        msgDepth = depth()


        msg.x_mode = True
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.z_setpoint = 3

        while(msgDepth < 3):

            time.sleep(0.1)

        return "finished"


class StateMachine(Node):
    def __init__(self):
        super().__init__("state_machine_node")

        self.depth_sensor_subscriber = self.create_subscription(
            Float32, "depth", self.depth_sensor_cb, 10
        )

        # terminal outcomes
        self.state_machine = StateMachine(outcomes={"complete"})

        self.currentDepth = 0

        self.state_machine.add_state("START", StartingState(), transitions={"finished" : "IDK"})

        self.state_machine.set_start_state("START")

        self.yasmin_pub = YasminViewerPub(self.state_machine, "TigerFish_SM")

        self.timer = self.create_timer(0.1, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")

    def getDepth(self):
        return self.currentDepth
    
    def depth_sensor_cb(self, msg: Float32):
        self.get_logger().info(f"{msg.data}")
        self.currentDepth = msg.data


def main(args=None):
    rclpy.init(args=args)
    node = StateMachine()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()