from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float32, String # pyright: ignore[reportMissingImports]

import rclpy
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT
)

qos_controller = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        # self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self._odom_cb, 10)
        
        # self.motor_publisher = self.create_publisher(
        #     Float32MultiArray,
        #     "motor_powers",
        #     qos
        # )
        
        self.controller_subscriber = self.create_subscription(
            String,
            'command_line',
            self.command_line_cb,
            qos_controller
        )
        
        # self.servo_publisher = self.create_publisher(
        #     Float32, 
        #     "topic_servo_angle",
        #     10
        # )
        
        period = 1.0 / 10.0
        self.timer = self.create_timer(period, self._timer_cb)
        self.start_time = time.time()
        self.switch_time = 3
        
    def _timer_cb(self):
        return
        power = 0.4
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