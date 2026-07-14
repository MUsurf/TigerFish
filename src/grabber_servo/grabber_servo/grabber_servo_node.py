import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import Jetson.GPIO as GPIO

FREQ = 200.0
PIN = 33  # Replace with the actual BOARD pin number

MAX_ANGLE = 25.0

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN, GPIO.OUT)


class ServoControllerNode(Node):
    def __init__(self):
        super().__init__("servo_controller")

        self.pwm = GPIO.PWM(PIN, FREQ)
        self.pwm.start(self.get_duty_cycle(0.0))

        self.mode_subscriber = self.create_subscription(
            String,
            "servo_mode",
            self.servo_mode_cb,
            10,
        )

    def get_duty_cycle(self, angle: float) -> float:
        angle += 90.0

        pulse_width_us = ((180.0 - angle) / 180.0) * 2000.0 + 500.0

        return pulse_width_us * FREQ / 1_000_000.0 * 100.0

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

        self.pwm.ChangeDutyCycle(self.get_duty_cycle(angle))
        


def main(args=None):
    rclpy.init(args=args)
    servo_controller = ServoControllerNode()

    try:
        rclpy.spin(servo_controller)
    except KeyboardInterrupt:
        pass
    finally:
        servo_controller.pwm.stop()
        GPIO.cleanup()
        servo_controller.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()