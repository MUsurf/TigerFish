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

        # Declare parameters
        self.declare_parameter("servo_pin", 32)
        self.declare_parameter("min_angle", 0.0) 
        self.declare_parameter("max_angle", 60) # recomended open angle (can be tested)
        self.declare_parameter("pwm_frequency", 50) #Hz #! Where this number from
        self.declare_parameter("min_duty_cycle", 2.5) #! Where this number from
        self.declare_parameter("max_duty_cycle", 12.5) #! Where this number from

        # Load parameters
        self.servo_pin = self.get_parameter("servo_pin").value
        self.min_angle = self.get_parameter("min_angle").value
        self.max_angle = self.get_parameter("max_angle").value
        self.min_duty_cycle = self.get_parameter("min_duty_cycle").value
        self.max_duty_cycle = self.get_parameter("max_duty_cycle").value
        pwm_frequency = self.get_parameter("pwm_frequency").value

        # Jetson GPIO setup (BOARD numbering)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.servo_pin, GPIO.OUT)

        # PWM device (duty cycle is 0–100) 
        self.pwm = GPIO.PWM(self.servo_pin, pwm_frequency) 
        self.pwm.start(0)

        # Subscriber
        self.subscribedTopic = "servo_angle_input" 

        self.subscription = self.create_subscription(
            Float32, self.subscribedTopic, self.angle_callbackFunction, servo_qos
        )

        self.kill_subscriber = self.create_subscription(
            Bool, "kill", self.kill_cb, kill_qos
        )

        # Publisher
        self.publisherTopic = "servo_angle_feedback" #! again does not need the topic. And if one is called feedback, one should be called input
        self.feedback_publisher = self.create_publisher(
            Float32,
            self.publisherTopic,
            10,  # self.queueSize
        )

        self.current_angle = self.max_angle 
        initial_duty = self.angle_to_duty_cycle(self.max_angle)
        self.pwm.ChangeDutyCycle(initial_duty)

    def angle_to_duty_cycle(self, angle):
        angle = max(self.min_angle, min(angle, self.max_angle))

        # Convert angle to duty cycle percentage
        duty_percent = self.min_duty_cycle + ( (angle - self.min_angle) / (self.max_angle - self.min_angle)) * (self.max_duty_cycle - self.min_duty_cycle)  
        # Add duty cycle offset
        # Normalize within our duty cycle range
        # Normalize within our min/max angle range
        #! Wtf is this styling 
        """
        !duty_percent = self.min_duty_cycle + ((angle - self.min_angle) / (self.max_angle - self.min_angle))
        !duty_percent = duty_percent * (self.max_duty_cycle - self.min_duty_cycle)
        !
        !is a lot better.
        !"""
        
        #! Now i can flame it. What is the point of this whole thing?
        #! Why is there a duty cycle offset? Why is there a duty cycle range?
        #! The only part obvious is the min max angle range.
        #! Why everything else though? It might not be wrong, but i cannot see why or what function it serves.
        

        return duty_percent  # Jetson expects 0–100 duty cycle #! correct

    def angle_callbackFunction(self, msg_angle):
        angle = msg_angle.data
        self.get_logger().info(f"Received angle command: {angle}") #! Don't need this unless we are debugging. Adds a lot of clutter

        duty = self.angle_to_duty_cycle(angle)
        self.pwm.ChangeDutyCycle(duty)

        self.current_angle = max(self.min_angle, min(angle, self.max_angle))

        feedback_msg = Float32()
        feedback_msg.data = self.current_angle
        self.feedback_publisher.publish(feedback_msg) 
        #! This "feedback_msg" has no purpose. It immediately returns the angle we just passed in, it isn't actually feedback.
        #! And also it only happens once, immediately in this callback after setting the angle
        #! Why did you keep this?

    def destroy_node(self):
        self.pwm.stop()
        GPIO.cleanup()
        super().destroy_node()
        #! Looks fine

    def kill_cb(self, msg):
        if msg.data:
            self.get_logger().warn("Servo kill received — shutting down.")
            rclpy.shutdown()
        #! Looks fine


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