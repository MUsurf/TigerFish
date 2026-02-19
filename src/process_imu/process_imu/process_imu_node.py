#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Imu

ALPHA = 0.2
yaw = math.radians(45) # This should be for a 45 degree yaw rotate :)
# IMU_TO_BODY_Q = (0.0, 0.0, math.sin(yaw/2), math.cos(yaw/2))
IMU_TO_BODY_Q = (0.0, 0.0, 0.0, 1.0)

WAIT_COUNT = 75
BIAS_COUNT = 75

class ProcessImuNode(Node):
    def __init__(self):
        super().__init__('process_imu_node')
        self.imu_sub = self.create_subscription(Imu, "imu_data", self._imu_cb, 10)
        self.imu_pub = self.create_publisher(Imu, "processed_imu_data", 10)


        self.prev_orientation = None
        self.prev_ang_vel = None
        self.prev_lin_accel = None
        
        self.alpha = ALPHA
        self.frame_id = 'base_link'
        
        self.mount_q = self._normalize_quat(*IMU_TO_BODY_Q)
        self.mount_R = self._quat_to_rotmat(self.mount_q)
        
        self.g_bias_list = [(0.0, 0.0, 0.0) for _ in range(BIAS_COUNT)]
        self.a_bias_list = [(0.0, 0.0, 0.0) for _ in range(BIAS_COUNT)]
        
        self.bias_counter = 0
        self.a_bias = 0.0
        self.g_bias = 0.0
        self.wait_counter = 0
        
        self.get_logger().info('Initialized Process Imu :)')
        
    def _normalize_quat(self, x, y, z, w):
        norm = math.sqrt(x * x + y * y + z * z + w * w)
        if norm == 0.0:
            return 0.0, 0.0, 0.0, 1.0
        return x / norm, y / norm, z / norm, w / norm
    
    def _low_pass(self, prev, current, alpha):
        """Exponential moving average: prev + alpha*(current - prev)."""
        if prev is None:
            return current
        return tuple(p + alpha * (c - p) for p, c in zip(prev, current))
    
    def _quat_multiply(self, q1, q2):
        """Multiply two quaternions q1 * q2"""
        x1, y1, z1, w1 = q1
        x2, y2, z2, w2 = q2

        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        return (x, y, z, w)

    def _quat_to_rotmat(self, q):
        """Convert quaternion (x, y, z, w) to a 3x3 rotation matrix."""
        x, y, z, w = q
        xx = x * x
        yy = y * y
        zz = z * z
        xy = x * y
        xz = x * z
        yz = y * z
        wx = w * x
        wy = w * y
        wz = w * z

        return [
            [1.0 - 2.0*(yy + zz), 2.0*(xy - wz),       2.0*(xz + wy)],
            [2.0*(xy + wz),       1.0 - 2.0*(xx + zz), 2.0*(yz - wx)],
            [2.0*(xz - wy),       2.0*(yz + wx),       1.0 - 2.0*(xx + yy)],
        ]

    def _rotate_vec(self, R, v):
        """Rotate a 3D vector v by rotation matrix R (3x3)."""
        vx, vy, vz = v
        return (
            R[0][0]*vx + R[0][1]*vy + R[0][2]*vz,
            R[1][0]*vx + R[1][1]*vy + R[1][2]*vz,
            R[2][0]*vx + R[2][1]*vy + R[2][2]*vz,
        )


    def _imu_cb(self, msg : Imu):
        if self.wait_counter < WAIT_COUNT:
            self.wait_counter+=1
            return
        if self.bias_counter < BIAS_COUNT:
            self.a_bias_list[self.bias_counter] = (
                msg.linear_acceleration.x,
                msg.linear_acceleration.y,
                msg.linear_acceleration.z,
            )

            self.g_bias_list[self.bias_counter] = (
                msg.angular_velocity.x,
                msg.angular_velocity.y,
                msg.angular_velocity.z,
            )
            self.bias_counter+=1
            if self.bias_counter == BIAS_COUNT:
                # I don't want to use numpy rn, trust me
                self.a_bias = tuple(sum(vals)/len(self.a_bias_list) for vals in zip(*self.a_bias_list))
                self.g_bias = tuple(sum(vals)/len(self.g_bias_list) for vals in zip(*self.g_bias_list))
            else:
                return
            
        qx = msg.orientation.x
        qy = msg.orientation.y
        qz = msg.orientation.z
        qw = msg.orientation.w
        qx, qy, qz, qw = self._normalize_quat(qx, qy, qz, qw)
        current_orientation = (
            qx, 
            qy, 
            qz, 
            qw
        )
        current_ang_vel = (
            msg.angular_velocity.x - self.g_bias[0],
            msg.angular_velocity.y - self.g_bias[1],
            msg.angular_velocity.z - self.g_bias[2],
        )
        current_linear_accel = (
            msg.linear_acceleration.x - self.a_bias[0],
            msg.linear_acceleration.y - self.a_bias[1],
            msg.linear_acceleration.z - self.a_bias[2],
        )
        filt_orientation = self._low_pass(self.prev_orientation, current_orientation, self.alpha)
        filt_ang_vel = self._low_pass(self.prev_ang_vel, current_ang_vel, self.alpha)
        filt_linear_accel = self._low_pass(self.prev_lin_accel, current_linear_accel, self.alpha)
        self.prev_orientation = filt_orientation
        self.prev_ang_vel = filt_ang_vel
        self.prev_lin_accel = filt_linear_accel
        
        # Rotate and pray
        filt_orientation = self._normalize_quat(*filt_orientation)
        filt_orientation = self._quat_multiply(self.mount_q, filt_orientation)

        filt_ang_vel = self._rotate_vec(self.mount_R, filt_ang_vel)
        filt_linear_accel = self._rotate_vec(self.mount_R, filt_linear_accel)

        
        filtered_msg = Imu()
        filtered_msg.header.stamp = msg.header.stamp
        filtered_msg.header.frame_id = self.frame_id
        
        filtered_msg.orientation.x, filtered_msg.orientation.y, filtered_msg.orientation.z, filtered_msg.orientation.w = filt_orientation
        filtered_msg.angular_velocity.x, filtered_msg.angular_velocity.y, filtered_msg.angular_velocity.z = filt_ang_vel
        filtered_msg.linear_acceleration.x, filtered_msg.linear_acceleration.y, filtered_msg.linear_acceleration.z = filt_linear_accel
        
        # Legit don't use these yet. DVL incoming though TRUST
        filtered_msg.orientation_covariance = list(msg.orientation_covariance)
        filtered_msg.angular_velocity_covariance = list(msg.angular_velocity_covariance)
        filtered_msg.linear_acceleration_covariance = list(msg.linear_acceleration_covariance)
        
        self.imu_pub.publish(filtered_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ProcessImuNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()
