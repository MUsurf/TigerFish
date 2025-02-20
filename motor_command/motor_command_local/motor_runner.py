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

# num_motors = 8

# high: List[int] = [20 for i in range(num_motors)]
# low: List[int] = [30 for i in range(num_motors)]
# list_thing = high


# hl_counter = 0

# def commander():
#     global hl_counter
#     # pub = rospy.Publisher(Int32MultiArray, 'motor_command', 10)
#     # rospy.init_node('motor_commander', anonymous=True)
#     rclpy.init(args=sys.argv)
#     node = rclpy.create_node('motor_commander')

#     node.get_logger().info('Created node')
#     node.Publisher(Int32MultiArray, 'motor_command', 10)
#     rate = rospy.Rate(.1) # 10hz

#     #! This is just a section to show the motors running when there is seperate input from ros this should not be used
#     while rclpy.ok():#not rospy.is_shutdown():
#         if (hl_counter == 0):
#             list_thing = high
#         else:
#             list_thing = low
#         hl_counter = (hl_counter + 1) % 2
#         # hello_str = "hello world %s" % rospy.get_time()
#         rospy.loginfo(list_thing)
#         pub.publish(data=list_thing)
#         rate.sleep()

# if __name__ == '__main__':
#     try:
#         commander()
#     except rospy.ROSInterruptException:
#         pass




class MotorCommander(Node):
    def __init__(self):
        super().__init__('motor_commander')
        self.publisher = self.create_publisher(Int32MultiArray, 'motor_command', 10)
        self.timer = self.create_timer(10.0, self.timer_callback)  # 0.1 Hz
        
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