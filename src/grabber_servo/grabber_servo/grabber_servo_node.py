# Begin imports
import rclpy

# End imports
from rclpy.node import Node
from std_msgs.msg import Float32, Bool
# from gpiozero import PWMOutputDevice  # not for Jetson

import Jetson.GPIO as GPIO  # for Jetson

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

servo_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
)

class ServoControllerNode(Node):
    def __init__(self):
        super().__init__("servo_controller")

        # Load parameters
        self.servo_pin = 32 #! this might be a lie
        self.pwm_frequency = 50 # Hz

        # Jetson GPIO setup (BOARD numbering)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.servo_pin, GPIO.OUT)

        # PWM device (duty cycle is 0–100) 
        self.pwm = GPIO.PWM(self.servo_pin, self.pwm_frequency) 
        self.pwm.start(50)

        # Subscriber
        self.subscribedTopic = "servo_angle_input" 

        self.subscription = self.create_subscription(
            Float32, self.subscribedTopic, self.angle_callbackFunction, servo_qos
        )

        self.kill_subscriber = self.create_subscription(
            Bool, "kill", self.kill_cb, kill_qos
        )

    def angle_to_duty_cycle(self, angle):
        return max(0, min(angle / 1.8, 40))

    def angle_callbackFunction(self, msg_angle):
        angle = msg_angle.data

        duty = self.angle_to_duty_cycle(angle)
        self.pwm.ChangeDutyCycle(duty)

    def destroy_node(self):
        self.pwm.stop()
        GPIO.cleanup()
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
        
    #! This looks fine

if __name__ == "__main__":
    main()

    """Test (open close open) in terminal
# Open (max angle)
ros2 topic pub --once /servo_angle_input std_msgs/msg/Float32 "data: 55"

# Close (min angle)
ros2 topic pub --once /servo_angle_input std_msgs/msg/Float32 "data: 0.0"

ros2 topic pub --once /servo_angle_input std_msgs/msg/Float32 "data: 60"
    """