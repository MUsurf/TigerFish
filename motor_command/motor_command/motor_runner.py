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

OFF = [0 for _ in range(8)]

class IMUPower:
    def __init__(self, max_power, max_measurement):
        # Initialize I2C and BNO055 sensor
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(i2c, address=0x28)
        
        # Store initial yaw for get_power2
        self.initial_yaw = None
        
        # Current roll, pitch, yaw
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.max_power = max_power
        self.max_measurement = max_measurement

    def update(self):
        """Read current Euler angles from the BNO055."""
        euler = self.sensor.euler  # Returns (heading, roll, pitch)
        if euler is None:
            # Sensor not ready yet
            return
        
        heading, roll, pitch = euler
        self.roll = roll
        self.pitch = pitch
        self.yaw = heading
        
        # Store initial yaw at first update
        if self.initial_yaw is None:
            self.initial_yaw = self.yaw

    def _map_angle_to_power(self, angle):
        """Maps 0 → max_angle to 0–20 linearly, caps above max_angle."""
        abs_angle = abs(angle)
        if abs_angle >= self.max_measurement:
            return self.max_power
        return (abs_angle / self.max_measurement) * self.max_power

    def get_power(self):
        """
        Returns a value 0–20 based on roll/pitch tilt.
        0 = flat, 20 = tilt >= 45 degrees.
        Uses the larger of absolute roll or pitch.
        """
        return self._map_angle_to_power(max(abs(self.roll), abs(self.pitch)))

    def get_power2(self):
        """
        Returns a value 0–20 based on yaw relative to initial yaw.
        0 = initial yaw, 20 = >45 degrees yaw change.
        """
        if self.initial_yaw is None:
            return 0
        # Compute minimal angle difference (wrap around 360)
        delta_yaw = (self.yaw - self.initial_yaw + 180) % 360 - 180
        return self._map_angle_to_power(delta_yaw)

class Sequence():
    def __init__(self, data, duration, pre_wait, post_wait):
        self.data = data
        self.duration = duration
        self.pre_wait = pre_wait
        self.post_wait = post_wait
        self.start_time = None
        
    def start(self):
        self.start_time = time.time()
        
    def do(self):
        if not self.activated : return None
        
        time_elapsed = time.time() - self.start_time
        
        if time_elapsed < self.pre_wait or time_elapsed > self.pre_wait + self.duration:
            if time_elapsed > self.pre_wait + self.duration + self.post_wait:
                self.start_time = None
                return OFF
            return OFF
        else:
            return self.data
        
    def stop(self):
        self.start_time = None
        
    def activated(self) : return self.start_time is not None
        



class MotorRunner(Node):
    def __init__(self):
        super().__init__('motor_commander')
        self.publisher = self.create_publisher(Float32MultiArray, 'motor_command', 10)
        self.timer = self.create_timer(0.05, self.timer_callback)
        
        self.num_motors = 8
    
        self.imu = IMUPower(35, 60)
        
        self.sequences = [Sequence([20 for i in range(8)], 1.0, 5.0, 500.0)]
        self.current_sequence = 0
        
        self.get_logger().info('MotorCommander Node Created')
        
        self.mode = 'IMU'
    
    def timer_callback(self):
        match self.mode:
            case 'IMU':
                data = self.do_imu()
                self.publish_data(data)
            case 'SEQUENCES':
                current_sequence = self.sequences[self.current_sequence]
                if not current_sequence.activated():
                    self.current_sequence = (self.current_sequence + 1) % len(self.sequences)
                    current_sequence = self.sequences[self.current_sequence]
                    current_sequence.start()
                data = current_sequence.do()
                if data is None : data = OFF
                self.publish_data(data)
            case _:
                self.publish_data(OFF)
        
    def do_imu(self):
        self.imu.update()
        power = self.imu.get_power()
        if power < 0 : power = 0
        if power > 35 : power = 35
        data = [power for _ in range(8)]
        return data
        
    def publish_data(self, data):
        msg = Float32MultiArray()
        msg.data = data
        
        self.get_logger().info(f'Publishing: {msg.data}')
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = MotorRunner()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down MotorCommander")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
