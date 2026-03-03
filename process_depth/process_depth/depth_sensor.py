#!/usr/bin/python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import ms5837

# this prob right
class DepthSensorNode(Node):
    def __init__(self):
        super().__init__('depth_sensor_node')

        self.publisher_ = self.create_publisher(Float32, 'depth_m', 10)
        self.sensor = ms5837.MS5837_30BA()

        if not self.sensor.init():
            self.get_logger().error('Sensor could not be initialized')
            raise RuntimeError('MS5837 init failed')

        # 20 hz as per the drewsters request
        self.timer = self.create_timer(0.05, self.publish_depth)
        self.get_logger().info('Depth sensor node started')

    def publish_depth(self):
        if not self.sensor.read():
            self.get_logger().warning('Sensor read failed')
            return

        msg = Float32()
        msg.data = float(self.sensor.depth())  # meters
        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = DepthSensorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()