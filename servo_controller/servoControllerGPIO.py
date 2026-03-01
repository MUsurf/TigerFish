# Begin imports
import rclpy
import RPi.GPIO as GPIO
from std_msgs.msg import Float64

# End imports
from rclpy.node import Node


class ServoControllerNode(Node):
    def __init__(self):
        # Init attributes of parent class
        super().__init__("servo_controller")

        # Declare parameters
        # This style allows dynamic changes (as opposed to hardcoding with =)
        self.declare_parameter("servo_pin", 18)  # I/O pin number
        self.declare_parameter("min_angle", 0.0)
        self.declare_parameter("max_angle", 180.0)
        self.declare_parameter("pwm_frequency", 50)
        self.declare_parameter("min_duty_cycle", 2.0)
        self.declare_parameter("max_duty_cycle", 12.0)

        self.servo_pin = self.get_parameter("servo_pin").value

        # Hardware Interface
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.servo_pin, self.get_parameter("pwm_frequency").value)
        self.pwm.start(0)  # Init to 0% duty cycle to prevent unexpected behavior

        # Name must match publisher node
        self.subscribedTopic = "topic_servo_angle"

        self.queueSize = 10  # 10 is small enough so that we ignore older commands in the event of lag/long movement times

        # Create the subscriber, which receives the current angle
        self.subscription = self.create_subscription(
            Float64, self.subscribedTopic, self.angle_callbackFunction, self.queueSize
        )
        self.subscription  # Prevent unused variable warning

        self.publisherTopic = "topic_servo_angle_feedback"
        # Create the publisher, which publishes a new desired position
        self.feedback_publisher = self.create_publisher(
            self.Float64, self.publisherTopic, self.queueSize
        )

    # Convert angle in degrees to PWM duty cycle
    def angle_to_duty_cycle(self, angle):
        angle = max(
            self.min_angle, min(angle, self.max_angle)
        )  # Ensure angle is within our defined range
        duty = 2 + (angle / 180.0) * 10
        return duty  # Transition when we know min/max --> max(self.min_duty_cycle, min(duty, self.max_duty_cycle))

    # Callback function that takes received angle
    def angle_callbackFunction(self, msg_angle):
        angle = msg_angle.data  # Input message is the desired angle
        self.get_logger().info(f"Received angle command: {angle}")
        duty = self.angle_to_duty_cycle(angle)
        self.pwm.ChangeDutyCycle(duty)
        self.current_angle = angle

        feedback_msg = Float64()
        feedback_msg.data = self.current_angle
        self.feedback_publisher.publish(feedback_msg)

    def destroy_node(self):
        self.pwm.stop()
        GPIO.cleanup()
        super().destroy_node()


# Main function; entry point
def main(args=None):
    # init rclpy
    rclpy.init(args=args)
    servo_controller = ServoControllerNode()

    try:
        # Spin node, callback timer function is called recursively
        rclpy.spin(servo_controller)
    except KeyboardInterrupt:
        pass
    finally:
        print("Servo_Controller spin failure.")
        servo_controller.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
