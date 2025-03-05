#!/usr/bin/env python3

'''
ROS
---

node:
----
        - motor_commander

Publishes:
---------
        - motor_command

Subscribes:
----------

'''


"""

! This is just a test driver function not used in comp

"""



# BEGIN IMPORT
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
# END IMPORT

from typing import List


class MotorCommander(Node):
    def __init__(self):
        super().__init__('motor_commander')
        self.publisher = self.create_publisher(Int32MultiArray, 'motor_command', 10)
        self.timer = self.create_timer(5.0, self.timer_callback)  # 0.1 Hz
        
        self.num_motors = 8
        self.high: List[int] = [20 for _ in range(self.num_motors)]
        self.low: List[int] = [30 for _ in range(self.num_motors)]
        self.list_thing = self.high
        self.hl_counter = 0
        
        self.get_logger().info('MotorCommander Node Created')
    
    def timer_callback(self):
        self.list_thing = self.high if self.hl_counter == 0 else self.low
        self.hl_counter = (self.hl_counter + 1) % 2
        
        msg = Int32MultiArray()
        msg.data = self.list_thing
        
        self.get_logger().info(f'Publishing: {msg.data}')
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MotorCommander()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down MotorCommander")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()