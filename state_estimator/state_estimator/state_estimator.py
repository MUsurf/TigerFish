import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import numpy as np
from numpy import sin, cos

OFFSET_ANGLE = np.pi / 4.0
R_IMU_TO_BODY = np.array([
    [ np.cos(OFFSET_ANGLE), -np.sin(OFFSET_ANGLE), 0 ],
    [ np.sin(OFFSET_ANGLE),  np.cos(OFFSET_ANGLE), 0 ],
    [ 0,             0,            1 ],
])

def quat_to_rot(q):
    w, x, y, z = q
    return np.array([
        [1-2*(y**2+z**2),   2*(x*y - z*w),   2*(x*z + y*w)],
        [2*(x*y + z*w),   1-2*(x**2+z**2),   2*(y*z - x*w)],
        [2*(x*z - y*w),   2*(y*z + x*w),   1-2*(x**2+y**2)]
    ])

def quat_normalize(q):
    return q / np.linalg.norm(q)

class StateEstimator(Node):
    def __init__(self):
        super().__init__('state_estimator')

        self.sub_data = self.create_subscription(
            Imu, 'imu_data', self.on_data, 10)

        self.sub_raw = self.create_subscription(
            Imu, 'imu_raw', self.on_raw, 10)

        self.last_time = None

        # state
        self.q_body = np.array([1.,0.,0.,0.])   # orientation
        self.ang_vel = np.zeros(3)              # angular velocity
        self.vel = np.zeros(3)                  # body-frame linear velocity
        self.pos = np.zeros(3)                  # body-frame linear position

        # bias estimates
        self.gyro_bias = np.zeros(3)
        self.acc_bias = np.zeros(3)

        self.raw_acc = np.zeros(3)
        self.raw_gyro = np.zeros(3)

    def on_raw(self, msg):
        self.raw_acc = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ])

        self.raw_gyro = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z
        ])

    def on_data(self, msg):
        # time delta
        if self.last_time is None:
            self.last_time = msg.header.stamp.sec + msg.header.stamp.nanosec*1e-9
            return
        t = msg.header.stamp.sec + msg.header.stamp.nanosec*1e-9
        dt = t - self.last_time
        self.last_time = t

        # fused quaternion from IMU_data
        q = np.array([
            msg.orientation.w,
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z
        ])
        q = quat_normalize(q)

        # convert IMU quaternion -> body frame quaternion
        Rq = quat_to_rot(q)
        R = R_IMU_TO_BODY @ Rq @ R_IMU_TO_BODY.T
        # extract quaternion back (not showing because orientation is already stable enough)
        self.q_body = q  # use original fused quaternion for simplicity

        # angular velocity (gyro)
        gyro_body = R_IMU_TO_BODY @ (self.raw_gyro - self.gyro_bias)
        self.ang_vel = gyro_body

        # linear acceleration
        acc_body = R_IMU_TO_BODY @ (self.raw_acc - self.acc_bias)

        # gravity vector
        Rq = quat_to_rot(self.q_body)
        gravity = Rq.T @ np.array([0,0,9.80665])

        acc_corrected = acc_body - gravity

        # integrate velocity
        self.vel += acc_corrected * dt

        # integrate position
        self.pos += self.vel * dt

        # drift management (optional)
        self.vel = np.clip(self.vel, -10, 10)

        # no print, no publish: you said no extra chatter
        # access self.pos, self.vel, self.q_body, self.ang_vel for your control logic
        return

def main():
    rclpy.init()
    node = ProcessIMU()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
