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
import rosros as rospy
from std_msgs.msg import Int32MultiArray
# END IMPORT

from typing import List

num_motors = 8

high: List[int] = [20 for i in range(num_motors)]
low: List[int] = [30 for i in range(num_motors)]
list_thing = high


hl_counter = 0

def commander():
    global hl_counter
    pub = rospy.Publisher('motor_command', Int32MultiArray, queue_size=10)
    rospy.init_node('motor_commander', anonymous=True)
    rate = rospy.Rate(.1) # 10hz

    #! This is just a section to show the motors running when there is seperate input from ros this should not be used
    while not rospy.is_shutdown():
        if (hl_counter == 0):
            list_thing = high
        else:
            list_thing = low
        hl_counter = (hl_counter + 1) % 2
        # hello_str = "hello world %s" % rospy.get_time()
        rospy.loginfo(list_thing)
        pub.publish(data=list_thing)
        rate.sleep()

if __name__ == '__main__':
    try:
        commander()
    except rospy.ROSInterruptException:
        pass