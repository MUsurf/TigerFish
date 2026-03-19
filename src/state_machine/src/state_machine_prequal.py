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

        if(msgDepth.depth < 5):

            # goes down for 0.2 seconds at 0.2 power
            msg.x_mode = False
            msg.z_mode = False
            msg.roll_mode = False
            msg.pitch_mode = False
            msg.yaw_mode = False
            msg.y_power = -0.2

            time.sleep(0.2)

        return "finished"


class StateMachineNode(Node):
    def __init__(self):
        super().__init__("state_machine_node")

        # terminal outcomes
        self.state_machine = StateMachine(outcomes={"complete"})

        self.state_machine.add_state("START", StartingState(), transitions={"finished" : "IDK"})

        self.state_machine.set_start_state("START")

        self.yasmin_pub = YasminViewerPub(self.state_machine, "TigerFish_SM")

        self.timer = self.create_timer(0.1, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")


def main(args=None):
    rclpy.init(args=args)
    node = StateMachineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()