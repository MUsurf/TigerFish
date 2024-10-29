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
from motor_interface import MotorInterface
# remove 

# Begin imports
import rospy

from std_msgs.msg import Int32MultiArray
# End imports

# Rospy nodes
rospy.init_node("motor_listener")
rate = rospy.Rate(100)


# Motor init codes
try:
    # Set up for 8 motors should be typical set up
    # Next thing to do is mock the motors
    local_channels: List[int] = [x for x in range(8)]
    num_motors: int = len(local_channels)
    motor_caller = MotorInterface(local_channels, num_motors, 0, 100, .1, .5, 5)

    # high: List[int] = [20 for i in range(num_motors)]
    # low: List[int] = [30 for i in range(num_motors)]

    print("arming")
    motor_caller.arm_seq()
    print("done arming")
    while not rospy.is_shutdown():
        rospy.Subscriber("motor_command", Int32MultiArray, motor_caller.callback)
        # rospy.Subscriber("volt_low", Bool, loop.cut_motors)
        rospy.spin()
    motor_caller.clo_seq()

except KeyboardInterrupt:
    motor_caller.clo_seq()



