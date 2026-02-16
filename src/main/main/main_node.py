from nav_msgs.msg import Odometry
from rclpy.node import Node
import rclpy

class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self._odom_cb, 10)
        
    def _odom_cb(self, msg : Odometry):
        self.get_logger().info(f'X: {msg.pose.pose.position.x} Y: {msg.pose.pose.position.y} Z: {msg.pose.pose.position.z}')
        
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