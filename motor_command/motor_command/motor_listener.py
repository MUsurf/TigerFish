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

# Rospy nodes
# rospy.init_node("motor_listener")
# rclpy.init(args=sys.argv)
# node = rclpy.create_node('motor_listener')

# node.get_logger().info('Created node')

# # rate = rospy.Rate(100)
# rclpy.Rate(100, node.get_clock())


# # Motor init codes
# try:
#     # Set up for 8 motors should be typical set up
#     # Next thing to do is mock the motors
#     local_channels: List[int] = [x for x in range(8)]
#     num_motors: int = len(local_channels)
#     motor_caller = MotorInterface(local_channels, num_motors, 0, 100, .1, .5, 5)

#     # high: List[int] = [20 for i in range(num_motors)]
#     # low: List[int] = [30 for i in range(num_motors)]

#     print("arming")
#     motor_caller.arm_seq()
#     print("done arming")
#     while rclpy.ok():#not rospy.is_shutdown():
#         rospy.Subscriber("motor_command", Int32MultiArray, motor_caller.callback)
#         # rospy.Subscriber("volt_low", Bool, loop.cut_motors)
#         rclpy.spin(node)
#     motor_caller.clo_seq()

# except KeyboardInterrupt:
#     motor_caller.clo_seq()






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
        
        # self.timer = self.create_timer(0.01, self.timer_callback)  # 100Hz
        
        # Motor init codes
        self.local_channels: List[int] = [x for x in range(8)]
        self.num_motors: int = len(self.local_channels)
        self.motor_caller = MotorInterface(self.local_channels, self.num_motors, 0, 100, .1, .5, 5)
        
        self.get_logger().info("Arming motors")
        self.motor_caller.arm_seq()
        self.get_logger().info("Done arming")

    def motor_callback(self, msg: Int32MultiArray):
        self.get_logger().info(f'Received motor command: {msg.data}')
        self.motor_caller.callback(msg)

    def shutdown(self):
        self.get_logger().info("Shutting down motor listener")
        self.motor_caller.clo_seq()


def main(args=None):
    rclpy.init(args=args)
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

