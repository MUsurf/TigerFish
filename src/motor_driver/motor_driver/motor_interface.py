from motor_driver.motor_commander import MotorCommander, NUM_MOTORS
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray, Bool
from ament_index_python.packages import get_package_share_directory

import numpy as np
import time
import rclpy
import os
import json

kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

FREQ = 40  # hz
LOG_FREQ = 1  # hz
DELTA = 0.75  # per second

ARM_TIME = 2.0

STEP_SIZE = DELTA / FREQ

MAX_CURRENT = 10  # amps

DEADBAND = 0.01


class PowerConverter:
    def __init__(self):
        pkg_share = get_package_share_directory("motor_driver")
        json_path = os.path.join(pkg_share, "data/14.8V_T200_data.json")

        if not os.path.exists(json_path):
            raise FileNotFoundError(f"T200 JSON not found: {json_path}")

        with open(json_path, "r") as f:
            t200 = json.load(f)
        rows = t200["data"]

        pwm = np.asarray([r["pwm"] for r in rows], dtype=float)
        force = np.asarray([r["force"] for r in rows], dtype=float)
        current = np.asarray([r["current"] for r in rows], dtype=float)

        ok = current <= MAX_CURRENT
        force_temp = force[ok]

        self.max_force = abs(min(force_temp))
        ok2 = abs(force) <= self.max_force

        self.pwm = pwm[ok2]
        self.force = force[ok2]

        idx = np.argsort(self.force)
        self.force = self.force[idx]
        self.pwm = self.pwm[idx]

        if self.pwm.size < 5:
            raise ValueError("GIVE ME MORE CURRENT PLEASE BRO")

    def convert_power(self, power: float):
        if power == 0.0:
            return 0
        power = min(1, max(-1, power))

        pulse_width = np.interp(power * self.max_force, self.force, self.pwm)

        percent = 2 * ((pulse_width - 1100.0) / (1900.0 - 1100.0)) - 1

        return percent


class MotorInterface(Node):
    def __init__(self):
        super().__init__("motor_interface")

        self.motor_commander: MotorCommander = MotorCommander()

        self.motor_states = [0.0 for _ in range(NUM_MOTORS)]
        self.motor_goals = [0.0 for _ in range(NUM_MOTORS)]

        self.listening = True

        self.motor_power_subscriber = self.create_subscription(
            Float32MultiArray, "motor_powers", self.power_cb, QOS
        )

        self.kill_subscriber = self.create_subscription(
            Bool, "kill", self.kill_cb, kill_qos
        )

        self.timer = self.create_timer(1.0 / FREQ, self.timer_cb)
        self.logging_timer = self.create_timer(1.0 / LOG_FREQ, self.log_cb)

        self.arm_sequence()
        self.power_converter = PowerConverter()

        self.get_logger().info(
            f"Max power forward :{self.power_converter.convert_power(1.0)}"
        )
        self.get_logger().info(
            f"Max power rev :{self.power_converter.convert_power(1.0)}"
        )

    def arm_sequence(self):
        self.set_motor_goals([0.0 for _ in range(NUM_MOTORS)])
        time.sleep(ARM_TIME)

    def timer_cb(self):
        self.step_motors()

    def log_cb(self):
        self.get_logger().info(f"Motor goals: {self.motor_goals}")

    def step_motors(self):
        next_motor_powers = [0.0 for _ in range(NUM_MOTORS)]

        for i, (goal, state) in enumerate(zip(self.motor_goals, self.motor_states)):
            distance = goal - state
            if abs(distance) < STEP_SIZE:
                next_motor_powers[i] = goal
            else:
                next_motor_powers[i] = (
                    state + ((distance > 0) - (distance < 0)) * STEP_SIZE
                )

        self.motor_states = next_motor_powers

        for i, p in enumerate(next_motor_powers):
            next_motor_powers[i] = p if abs(p) > DEADBAND else 0.0

        converted_powers = [
            self.power_converter.convert_power(p) for p in next_motor_powers
        ]
        self.motor_commander.set_motor_powers(converted_powers, 0.0)
        # self.get_logger().info(f'{converted_powers[0]}')

    def power_cb(self, msg):
        self.set_motor_goals(msg.data)

    def set_motor_goals(self, powers: list) -> bool:
        if not self.listening or len(powers) != NUM_MOTORS:
            return False
        self.motor_goals = powers
        return True

    def stop(self):
        self.motor_goals = [0.0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_motor_powers([0.0 for _ in range(NUM_MOTORS)])
        self.motor_states = [0.0 for _ in range(NUM_MOTORS)]

    def kill_cb(self, msg: Bool):
        if msg.data:
            self.listening = False
            self.stop()
            time.sleep(0.1)
            raise Exception("Motors called to kill.")


def main(args=None):
    rclpy.init(args=args)
    node = MotorInterface()
    try:
        rclpy.spin(node)
    finally:
        node.stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
