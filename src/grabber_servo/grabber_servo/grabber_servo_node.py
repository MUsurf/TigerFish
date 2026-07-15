
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import board
import busio
from adafruit_pca9685 import PCA9685


FREQ = 200.0

PCA9685_ADDRESS = 0x41
SERVO_CHANNEL = 0

MAX_ANGLE = 25.0


class ServoControllerNode(Node):
    def __init__(self):
        super().__init__("servo_controller")

        self.i2c = busio.I2C(board.SCL, board.SDA)

        self.pca9685 = PCA9685(
            self.i2c,
            address=PCA9685_ADDRESS,
        )
        self.pca9685.frequency = int(FREQ)

        self.servo_channel = self.pca9685.channels[SERVO_CHANNEL]

        self.set_servo_angle(0.0)

        self.mode_subscriber = self.create_subscription(
            String,
            "servo_mode",
            self.servo_mode_cb,
            10,
        )

    def get_duty_cycle(self, angle: float) -> int:
        angle += 90.0

        pulse_width_us = (
            ((180.0 - angle) / 180.0) * 2000.0
            + 500.0
        )

        period_us = 1_000_000.0 / FREQ
        duty_fraction = pulse_width_us / period_us

        return int(duty_fraction * 0xFFFF)

    def set_servo_angle(self, angle: float):
        self.servo_channel.duty_cycle = self.get_duty_cycle(angle)

    def servo_mode_cb(self, message: String):
        match message.data:
            case "neutral":
                angle = 0.0
            case "left":
                angle = MAX_ANGLE
            case "right":
                angle = -MAX_ANGLE
            case _:
                return

        self.set_servo_angle(angle)
        
        self.get_logger().info(f'Angle: {angle}')

    def shutdown(self):
        # Disable the PWM output on channel 0.
        self.servo_channel.duty_cycle = 0

        self.pca9685.deinit()
        self.i2c.deinit()


def main(args=None):
    rclpy.init(args=args)
    servo_controller = ServoControllerNode()

    try:
        rclpy.spin(servo_controller)
    except KeyboardInterrupt:
        pass
    finally:
        servo_controller.shutdown()
        servo_controller.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()

