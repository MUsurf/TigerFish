#!/usr/bin/env python3

'''
ROS 
---

node:
-----
    - motor_listener

Publishes:
----------

Subscribes:
----------
    - motor_command

'''


# Begin typing imports
from typing import List
# End typing imports

# remove
from motor_command.motor_interface import MotorInterface
# remove 

# Begin imports
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
# End imports



class MotorListener(Node):
    def __init__(self):
        super().__init__('motor_listener')
        self.get_logger().info('Created node')
        
        self.subscription = self.create_subscription(
            Int32MultiArray,
            'motor_command',
            self.motor_callback,
            10  # QoS profile depth
        )
        self.get_logger().info('Created Subscriber')
        
        # Motor init codes
        self.local_channels: List[int] = [x for x in range(8)]
        self.num_motors: int = len(self.local_channels)
        self.motor_caller = MotorInterface(self.local_channels, self.num_motors, 0, 100, .1, .5, 5)
        
        self.get_logger().info("Arming motors")

        self.handle1 = self.motor_caller.arm_seq()
        self.motor_caller.second_setup()
        self.get_logger().info("Done arming")

    def motor_callback(self, msg: Int32MultiArray):
        self.get_logger().info(f'Received motor command: {msg.data}')
        self.motor_caller.callback(msg)

    def shutdown(self):
        self.get_logger().info("Shutting down motor listener")
        # May not bring motors down to zero
        self.motor_caller.stop_event.set()
        # Join thread back to main
        if self.handle1.is_alive():
            self.handle1.join(timeout=2)
        # Bring motors down to zero
        self.motor_caller.clo_seq()
        


def main(args=None):
    rclpy.init(args=args)
    print("Starting listener")
    node = MotorListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.shutdown()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

