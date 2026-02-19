from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray # pyright: ignore[reportMissingImports]

import rclpy

class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        # self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self._odom_cb, 10)
        
        self.motor_publisher = self.create_publisher(Float32MultiArray, "motor_powers", 10)
        
        period = 1.0 / 10.0
        self.timer = self.create_timer(period, self._timer_cb)
        
    def _timer_cb(self):
        powers = [0.50, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50]
        msg = Float32MultiArray()
        msg.data = powers
        self.motor_publisher.publish(msg)
        self.get_logger().info('Bang :)')
        
    def _odom_cb(self, msg : Odometry):
        # self.get_logger().info(f'p_x: {msg.pose.pose.position.x} p_y: {msg.pose.pose.position.y} p_z: {msg.pose.pose.position.z}')
        # self.get_logger().info(f'v_x: {msg.twist.twist.linear.x} v_y: {msg.twist.twist.linear.y} v_z: {msg.twist.twist.linear.z}')
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