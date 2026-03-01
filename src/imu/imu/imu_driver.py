#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu
from std_msgs.msg import Bool

import board
import busio
import adafruit_bno055

import time

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

BIAS_COUNT = 10


class ImuNode(Node):
    def __init__(self):
        super().__init__("imu_node")

        self.declare_parameter("frame_id", "imu_link")
        self.declare_parameter("rate", 100.0)

        self.frame_id = self.get_parameter("frame_id").value
        self.rate = float(self.get_parameter("rate").value)

        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(i2c)
        
                
        time.sleep(0.1)
        # IMU-only fusion (gyro + accel, no mag)
        self.sensor.mode = adafruit_bno055.IMUPLUS_MODE 

        # NDOF
        # self.sensor.mode = adafruit_bno055.NDOF_MODE

        self.imu_pub = self.create_publisher(Imu, "imu_data", 10)

        period = 1.0 / self.rate if self.rate > 0 else 0.01
        self.timer = self.create_timer(period, self._timer_cb)
        
        self.kill_subscriber = self.create_subscription(
            Bool,
            'kill',
            self.kill_cb,
            kill_qos
        )
        
        
    def _timer_cb(self):
        # Get data from the $5 sensor
        quat = self.sensor.quaternion   
        accel = self.sensor.linear_acceleration  
        gyro = self.sensor.gyro
        #calib = self.sensor.calibration_status  # (sys, gyro, accel, mag)

        if quat is None or accel is None or gyro is None:
            self.get_logger().warn("IMU read returned None, skipping publish")
            return
        if any(math.isnan(v) for v in accel + gyro + quat):
            return

        w, x, y, z = quat

        # Normalize just in case
        norm = math.sqrt(w*w + x*x + y*y + z*z)
        if norm > 0:
            w /= norm
            x /= norm
            y /= norm
            z /= norm

        now = self.get_clock().now().to_msg()

        imu_msg = Imu()
        imu_msg.header.stamp = now
        imu_msg.header.frame_id = self.frame_id

        imu_msg.orientation.w = w
        imu_msg.orientation.x = x
        imu_msg.orientation.y = y
        imu_msg.orientation.z = z

        ax, ay, az = accel
        imu_msg.linear_acceleration.x = ax
        imu_msg.linear_acceleration.y = ay
        imu_msg.linear_acceleration.z = az
        # self.get_logger().info(f'aX: {ax:.4f} aY: {ay:.4f} aZ: {az:.4f}')


        gx, gy, gz = gyro
        gx = gx
        gy = gy
        gz = gz

        imu_msg.angular_velocity.x = gx
        imu_msg.angular_velocity.y = gy
        imu_msg.angular_velocity.z = gz

        imu_msg.orientation_covariance = [0.0] * 9 # Prob need this asp
        imu_msg.angular_velocity_covariance = [0.0] * 9 # ^
        imu_msg.linear_acceleration_covariance = [0.0] * 9 # ^
            
        self.imu_pub.publish(imu_msg)
    
    def kill_cb(self):
        return

def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
