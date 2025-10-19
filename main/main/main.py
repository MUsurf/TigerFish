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
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
# END IMPORT

from typing import List

import board
import busio
import adafruit_bno055

from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

PITCH_KP = 0.1
ROLL_KP = 0.1
MIN_POWER = -50.0
MAX_POWER = 50.0
FREQUENCY = 10.0 # Hz

class IMUWrapper:
    def __init__(self):
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.vroll = 0.0
        self.vpitch = 0.0
        self.vyaw = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.az = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        
    def update(self, msg):
        self.roll = msg.data[0]
        self.pitch = msg.data[1]
        self.yaw = msg.data[2]
        self.vroll = msg.data[3]
        self.vpitch = msg.data[4]
        self.vyaw = msg.data[5]
        self.ax = msg.data[6]
        self.ay = msg.data[7]
        self.az = msg.data[8]
        self.vx = msg.data[9]
        self.vy = msg.data[10]
        self.vz = msg.data[11]
        self.x = msg.data[12]
        self.y = msg.data[13]
        self.z = msg.data[14]

def clamp_list(values: List[float], min_value: float, max_value: float) -> List[float]:
    """Clamp each value in the list to be within the specified min and max range."""
    return [max(min(v, max_value), min_value) for v in values]

class Main(Node):
    def __init__(self):
        super().__init__('main')
        self.imu = IMUWrapper()
        self.imu_subscriber = self.create_subscription(
            Float32MultiArray,
            'imu_data',
            self.imu.update,
            qos
        )
        self.motor_publisher = self.create_publisher(Float32MultiArray, 'motor_powers', qos)

        self.timer = self.create_timer(1.0 / FREQUENCY, self.timer_callback)
        
        self.get_logger().info("Main node started.")
        
    def timer_callback(self):
        """
        This is going to assume the following: 
        - Motors in order: top left, top right, bottom left, bottom right BIRDS EYE VIEW
        - Positive pitch is forward up
        - Positive roll is right down
        """
        
        pitch_correction = [-ROLL_KP, -ROLL_KP, ROLL_KP, ROLL_KP, 0, 0, 0, 0] * self.imu.pitch
        roll_correction = [-PITCH_KP, PITCH_KP, -PITCH_KP, PITCH_KP, 0, 0, 0, 0] * self.imu.roll
        powers = [pitch_correction[i] + roll_correction[i] for i in range(8)]
        powers = clamp_list(powers, MIN_POWER, MAX_POWER)
        self.motor_publisher.publish(Float32MultiArray(data=powers))

def main(args=None):
    rclpy.init(args=args)
    node = Main()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down main node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
