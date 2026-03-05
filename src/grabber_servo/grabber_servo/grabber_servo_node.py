# Begin imports
import rclpy
# End imports
from rclpy.node import Node
from std_msgs.msg import Float64, Bool
from gpiozero import PWMOutputDevice

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)


class ServoControllerNode(Node):
    def __init__(self):
        super().__init__('servo_controller')

        # Declare parameters
        self.declare_parameter('servo_pin', 18)
        self.declare_parameter('min_angle', 0.0)
        self.declare_parameter('max_angle', 83.94)
        self.declare_parameter('pwm_frequency', 50)
        self.declare_parameter('min_duty_cycle', 2.5)
        self.declare_parameter('max_duty_cycle', 12.5)

        # Load parameters
        self.servo_pin = self.get_parameter('servo_pin').value
        self.min_angle = self.get_parameter('min_angle').value
        self.max_angle = self.get_parameter('max_angle').value
        self.min_duty_cycle = self.get_parameter('min_duty_cycle').value
        self.max_duty_cycle = self.get_parameter('max_duty_cycle').value
        pwm_frequency = self.get_parameter('pwm_frequency').value

        # gpiozero PWM device (0.0–1.0 duty cycle range)
        self.pwm = PWMOutputDevice(self.servo_pin, frequency=pwm_frequency)

        # Subscriber
        self.subscribedTopic = 'topic_servo_angle'
        self.queueSize = 10

        self.subscription = self.create_subscription(
            Float64,
            self.subscribedTopic,
            self.angle_callbackFunction,
            self.queueSize
        )
        
        self.kill_subscriber = self.create_subscription(
            Bool,
            'kill',
            self.kill_cb,
            kill_qos
        )
        
        # Publisher
        self.publisherTopic = 'topic_servo_angle_feedback'
        self.feedback_publisher = self.create_publisher(
            Float64,
            self.publisherTopic,
            self.queueSize
        )

        self.current_angle = self.max_angle
        initial_duty = self.angle_to_duty_cycle(self.max_angle)
        self.pwm.value = initial_duty

    def angle_to_duty_cycle(self, angle):
        angle = max(self.min_angle, min(angle, self.max_angle))

        # Convert angle to duty cycle percentage
        duty_percent = self.min_duty_cycle + ( # Add duty cycle offset
            (angle - self.min_angle) /
            (self.max_angle - self.min_angle) # Normalize within our min/max angle range
        ) * (self.max_duty_cycle - self.min_duty_cycle) # Normalize within our duty cycle range

        # Convert percent to gpiozero 0.0–1.0 range
        return duty_percent / 100.0

    def angle_callbackFunction(self, msg_angle):
        angle = msg_angle.data
        self.get_logger().info(f'Received angle command: {angle}')

        duty = self.angle_to_duty_cycle(angle)
        self.pwm.value = duty

        self.current_angle = max(self.min_angle, min(angle, self.max_angle))

        feedback_msg = Float64()
        feedback_msg.data = self.current_angle
        self.feedback_publisher.publish(feedback_msg)

    def destroy_node(self):
        self.pwm.close()
        super().destroy_node()
        
    def kill_cb(self, msg):
        if msg.data:
            self.get_logger().warn("Servo kill received — shutting down.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    servo_controller = ServoControllerNode()

    try:
        rclpy.spin(servo_controller)
    except KeyboardInterrupt:
        pass
    finally:
        servo_controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()