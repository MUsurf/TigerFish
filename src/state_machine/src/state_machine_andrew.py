import time

import rclpy
from rclpy.node import Node

from yasmin.state import State
from yasmin.state_machine import StateMachine
from yasmin_viewer.yasmin_viewer_pub import YasminViewerPub

from messages.msg import PIDInput
from messages.msg import depth


class State1(State):
    def __init__(self):
        # valid outcomes for this state
        super().__init__(outcomes=["next_state"])

    def execute(self) -> str:
        
        timeMe = time.time()

        while(timeMe + 2 > time.time()):
             
            # do something

            print("state 1")

            time.sleep(0.08)

        return "next_state"

class State2(State):
    def __init__(self):
        # valid outcomes for this state
        super().__init__(outcomes=["next_state"])

    def execute(self) -> str:
        
        timeMe = time.time()

        while(timeMe + 2 > time.time()):
             
            # do something

            print("state 1")

            time.sleep(0.08)

        return "next_state"


class StateMachineNode(Node):
    def __init__(self):
        super().__init__("state_machine_node")

        # terminal outcomes
        self.state_machine = StateMachine(outcomes={"complete"})

        self.state_machine.add_state("STATE1", State1(), transitions={"next_state" : "STATE2"})

        self.state_machine.add_state("START2", State2(), transitions={"next_state" : "STATE1"})

        self.state_machine.set_start_state("STATE1")

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