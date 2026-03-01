from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float32, String # pyright: ignore[reportMissingImports]

import rclpy
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy
import numpy as np


qos = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT
)

qos_controller = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)

def rpy_from_quat(q):
    """
    Convert geometry_msgs.msg.Quaternion to roll, pitch, yaw (radians).
    
    Assumes quaternion fields:
        q.x, q.y, q.z, q.w
    Uses XYZ (roll, pitch, yaw) convention.
    """

    x = q.x
    y = q.y
    z = q.z
    w = q.w

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.sign(sinp) * (np.pi / 2.0)  # use 90° if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self._odom_cb, 10)
        
        self.motor_publisher = self.create_publisher(
            Float32MultiArray,
            "motor_powers",
            qos
        )
        
        # self.controller_subscriber = self.create_subscription(
        #     String,
        #     'command_line',
        #     self.command_line_cb,
        #     qos_controller
        # )
        
        # self.servo_publisher = self.create_publisher(
        #     Float32, 
        #     "topic_servo_angle",
        #     10
        # )
        
        period = 1.0 / 10.0
        self.timer = self.create_timer(period, self._timer_cb)
        self.start_time = time.time()
        self.switch_time = 2
        
    def _timer_cb(self):
        power = 0.1
        powers = [0.0 for _ in range(8)]
        time_elapsed = time.time() - self.start_time
        
        if (time_elapsed // self.switch_time) % 2 == 1:
            powers[int((time_elapsed // (2 * self.switch_time)) % 8)] = power
            # powers[0] = power
            # msg = Float32()
            # msg.data = 0.0
            # self.servo_publisher.publish(msg)
        else:
            powers = [0.0 for _ in range(8)] # Don't need this but i hate debugging
            # msg = Float32()
            # msg.data = 90.0
            # self.servo_publisher.publish(msg)
        
        msg = Float32MultiArray()
        msg.data = powers
        self.motor_publisher.publish(msg)
        
        
    def command_line_cb(self, msg : String):
        self.get_logger().info(msg.data)
        
    def _odom_cb(self, msg : Odometry):
        r, p, y = rpy_from_quat(msg.pose.pose.orientation)
        self.get_logger().info(f'roll: {r} pitch {p} yaw: {y}')
        return
        
        
def main(args=None):
    rclpy.init(args=args)
    node = MainNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()