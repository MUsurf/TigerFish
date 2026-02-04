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
from sensor_msgs.msg import Imu

# END IMPORT

from typing import List

import board
import busio
import adafruit_bno055

import math

from rclpy.qos import QoSProfile, ReliabilityPolicy

from pid_node.msg import Measurement, Setpoint, Mode

qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

FREQUENCY = 25.0 # Hz

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
        
    def update(self, msg : Imu):
        # Alright DID ChatGPT write this? I ain't gonna say nothing
        # --- Orientation (quaternion → roll, pitch, yaw) ---
        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        qw = msg.orientation.w

        # NED convention
        # roll  (x-axis rotation)
        sinr_cosp = 2.0 * (qw * qx + qy * qz)
        cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
        self.roll = math.atan2(sinr_cosp, cosr_cosp)

        # pitch (y-axis rotation)
        sinp = 2.0 * (qw * qy - qz * qx)
        if abs(sinp) >= 1:
            self.pitch = math.copysign(math.pi / 2, sinp)
        else:
            self.pitch = math.asin(sinp)

        # yaw (z-axis rotation, right-turn positive)
        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)

        # --- Angular velocity (body frame, rad/s) ---
        self.vroll = msg.angular_velocity.x
        self.vpitch = msg.angular_velocity.y
        self.vyaw = msg.angular_velocity.z

        # --- Linear acceleration (body frame, m/s²) ---
        self.ax = msg.linear_acceleration.x
        self.ay = msg.linear_acceleration.y
        self.az = msg.linear_acceleration.z

def clamp_list(values: List[float], min_value: float, max_value: float) -> List[float]:
    """Clamp each value in the list to be within the specified min and max range."""
    return [max(min(v, max_value), min_value) for v in values]

class Main(Node):
    def __init__(self):
        super().__init__('main')
        self.imu = IMUWrapper()
        self.imu_subscriber = self.create_subscription(
            Float32MultiArray,
            'processed_imu_data',
            self.imu.update,
            qos
        )
        self.mode_publisher = self.create_publisher(Mode, "pid_modes", 10)
        self.pos_measurement_publisher = self.create_publisher(Measurement, "position_measurements", 10)
        self.vel_measurement_publisher = self.create_publisher(Measurement, "velocity_measurements", 10)
        
        self.timer = self.create_timer(1.0 / FREQUENCY, self.timer_callback)
        
        self.get_logger().info("Main node started.")
        
    def timer_callback(self):
        modes = Mode()
        modes.x = False
        modes.y = False
        modes.z = False
        modes.roll = True
        modes.pitch = True
        modes.yaw = True
        
        self.mode_publisher.publish(modes)
        
        pos_m = Measurement()
        pos_m.x = self.imu.x
        pos_m.y = self.imu.y
        pos_m.z = self.imu.z
        pos_m.roll = self.imu.roll
        pos_m.pitch = self.imu.pitch
        pos_m.yaw = self.imu.yaw
        
        vel_m = Measurement()
        vel_m.x = self.imu.vx
        vel_m.y = self.imu.vy
        vel_m.z = self.imu.vz
        vel_m.roll = self.imu.vroll
        vel_m.pitch = self.imu.vpitch
        vel_m.yaw = self.imu.vyaw
        
        self.pos_measurement_publisher.publish(pos_m)
        self.vel_measurement_publisher.publish(vel_m)
        

    
        

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
