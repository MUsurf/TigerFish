import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import Jetson.GPIO as GPIO


PIN = 33
FREQ = 50.0
PERIOD_S = 1.0 / FREQ

MAX_ANGLE = 25.0


class ServoControllerNode(Node):
    def __init__(self):
        super().__init__("servo_controller")

        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PIN, GPIO.OUT, initial=GPIO.LOW)

        self.pulse_width_us = 1500
        self.running = True
        self.lock = threading.Lock()

        self.pwm_thread = threading.Thread(
            target=self.software_pwm_loop,
            daemon=True,
        )
        self.pwm_thread.start()

        self.mode_subscriber = self.create_subscription(
            String,
            "servo_mode",
            self.servo_mode_cb,
            10,
        )

        self.get_logger().info("Servo software PWM started on BOARD pin 33")

    def angle_to_pulse_us(self, angle: float) -> int:
        angle = max(-90.0, min(90.0, angle))

        # -90 degrees = 500 us
        #   0 degrees = 1500 us
        # +90 degrees = 2500 us
        return int(1500.0 + angle * (1000.0 / 90.0))

    def software_pwm_loop(self):
        while self.running:
            cycle_start = time.monotonic_ns()

            with self.lock:
                pulse_width_us = self.pulse_width_us

            GPIO.output(PIN, GPIO.HIGH)
            self.precise_sleep_us(pulse_width_us)
            GPIO.output(PIN, GPIO.LOW)

            next_cycle = cycle_start + int(PERIOD_S * 1_000_000_000)

            while self.running:
                remaining_ns = next_cycle - time.monotonic_ns()

                if remaining_ns <= 0:
                    break

                # Sleep normally until close to the next pulse.
                if remaining_ns > 300_000:
                    time.sleep((remaining_ns - 200_000) / 1_000_000_000)

    def precise_sleep_us(self, duration_us: int):
        end_ns = time.monotonic_ns() + duration_us * 1000

        while True:
            remaining_ns = end_ns - time.monotonic_ns()

            if remaining_ns <= 0:
                return

            if remaining_ns > 300_000:
                time.sleep((remaining_ns - 200_000) / 1_000_000_000)

    def servo_mode_cb(self, message: String):
        angles = {
            "neutral": 0.0,
            "left": MAX_ANGLE,
            "right": -MAX_ANGLE,
        }

        angle = angles.get(message.data)

        if angle is None:
            self.get_logger().warning(
                f"Unknown servo mode: {message.data!r}"
            )
            return

        pulse_width_us = self.angle_to_pulse_us(angle)

        with self.lock:
            self.pulse_width_us = pulse_width_us

        self.get_logger().info(
            f"Mode={message.data}, angle={angle}, "
            f"pulse={pulse_width_us} us"
        )

    def shutdown_servo(self):
        self.running = False

        if self.pwm_thread.is_alive():
            self.pwm_thread.join(timeout=1.0)

        GPIO.output(PIN, GPIO.LOW)
        GPIO.cleanup()


def main(args=None):
    rclpy.init(args=args)
    node = ServoControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown_servo()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()