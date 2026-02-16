from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from rclpy.node import Node

import rclpy

FREQ = 50.0 # Hz

class StateEstimator(Node):
    def __init__(self):
        super().__init__('state_estimator_node')
        
        self.imu_subscriber = self.create_subscription(Imu, "processed_imu_data", self._imu_cb, 10)
        self.odometry_publisher = self.create_publisher(Odometry, "state_estimation", 10)
        
        self.get_logger().info('Initialized state estimator.')
        
        self.current_odometry = None
        self.last_time = None
        
        period = 1.0 / FREQ
        self.timer = self.create_timer(period, self._timer_cb)
        
    def _timer_cb(self):
        if self.current_odometry is not None : self.odometry_publisher.publish(self.current_odometry)
        
    def _imu_cb(self, msg : Imu):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        
        if self.last_time is None:
            self.last_time = t
            self.current_odometry = Odometry()
            self.current_odometry.header.stamp = msg.header.stamp
            self.current_odometry.child_frame_id = 'base_link'
            self.current_odometry.header.frame_id = 'odom'
            self.current_odometry.pose.pose.orientation.w = 1.0
            return
        
        dt = t - self.last_time
        self.last_time = t
    
        o = Odometry()
        o.header.frame_id = 'odom'
        o.child_frame_id = 'base_link'
        o.header.stamp = msg.header.stamp
        
        o.twist.twist.angular = msg.angular_velocity
        o.twist.twist.linear.x = msg.linear_acceleration.x * dt + self.current_odometry.twist.twist.linear.x
        o.twist.twist.linear.y = msg.linear_acceleration.y * dt + self.current_odometry.twist.twist.linear.y
        o.twist.twist.linear.z = msg.linear_acceleration.z * dt + self.current_odometry.twist.twist.linear.z
        
        o.pose.pose.orientation = msg.orientation
        o.pose.pose.position.x = (
            self.current_odometry.pose.pose.position.x
            + 0.5 * (self.current_odometry.twist.twist.linear.x + o.twist.twist.linear.x) * dt
        )
        o.pose.pose.position.y = (
            self.current_odometry.pose.pose.position.y
            + 0.5 * (self.current_odometry.twist.twist.linear.y + o.twist.twist.linear.y) * dt
        )
        o.pose.pose.position.z = (
            self.current_odometry.pose.pose.position.z
            + 0.5 * (self.current_odometry.twist.twist.linear.z + o.twist.twist.linear.z) * dt
        )

        self.current_odometry = o
        
def main(args=None):
    rclpy.init(args=args)
    node = StateEstimator()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()

            
            
            