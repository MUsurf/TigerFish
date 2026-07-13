import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from gpiozero import PWMOutputDevice
import time

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

# placeholder numbers
DROP_LEFT_CYCLE = 2.5
DROP_RIGHT_CYCLE = 12.5
CLOSED_CYCLE = 7.5 
WAIT_SECONDS = 2.0

kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

trigger_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class DropperControllerNode(Node):
    def __init__(self):
        super().__init__("dropper_controller")

        # Declare parameters
        self.declare_parameter("servo_pin", 18)
        self.declare_parameter("pwm_frequency", 50)
        self.declare_parameter("closed_duty_cycle", CLOSED_CYCLE)
        self.declare_parameter("open_right_cycle", DROP_RIGHT_CYCLE)
        self.declare_parameter("open_left_cycle", DROP_LEFT_CYCLE)

        # Load parameters
        self.servo_pin = self.get_parameter("servo_pin").value
        pwm_frequency = self.get_parameter("pwm_frequency").value
        self.closed_duty_cycle = self.get_parameter("closed_duty_cycle").value
        self.open_right_duty_cycle = self.get_parameter("open_right_cycle").value
        self.open_left_duty_cycle = self.get_parameter("open_left_cycle").value

        # gpiozero PWM device (0.0-1.0 duty cycle range)
        self.pwm = PWMOutputDevice(self.servo_pin, frequency=pwm_frequency)

        # Subscriber: drop command
        self.drop_subscription = self.create_subscription(
            Bool, "drop", self.drop_callback, trigger_qos
        )

        # Subscriber: kill switch
        self.kill_subscription = self.create_subscription(
            Bool, "kill", self.kill_callback, kill_qos
        )

        self.has_dropped = False
        self.pwm.value = self.closed_duty_cycle / 100.0
        self.get_logger().info("Dropper armed and closed.")

    def drop_callback(self, msg):
        if not msg.data or self.has_dropped:
            return
        
        if not self.has_dropped:
            self.get_logger().info("Drop command received — opening.")
            self.pwm.value = self.open_right_duty_cycle / 100.0
            time.sleep(WAIT_SECONDS)
            self.pwm.value = self.open_left_duty_cycle / 100.0
            time.sleep(WAIT_SECONDS)
            self.pwm.value = self.closed_duty_cycle / 100.0
            self.has_dropped = True

    def kill_callback(self, msg):
        if msg.data:
            self.get_logger().warn("Kill received — shutting down.")
            rclpy.shutdown()

    def destroy_node(self):
        self.pwm.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    dropper_controller = DropperControllerNode()

    try:
        rclpy.spin(dropper_controller)
    except KeyboardInterrupt:
        pass
    finally:
        dropper_controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
    