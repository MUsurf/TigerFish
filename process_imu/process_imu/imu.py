# BEGIN IMPORT
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import threading
# END IMPORT


import board
import busio

from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

POLLING_RATE = 40  # Hz


# Decleration of wrapper for threading a function
def threaded(fn):
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


class IMUTracker(Node):
    def __init__(self, polling_rate: float):
        super().__init__("imu_tracker")
        self.polling_rate = polling_rate
        # Initialize I2C and BNO055 sensor
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bno055.BNO055_I2C(i2c, address=0x28)

        # Current roll, pitch, yaw
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.vroll = 0.0
        self.vpitch = 0.0
        self.vyaw = 0.0
        self.ax = 0.0
        self.ay = 0.0
        self.az = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self._last_update_time = time.time()

        self.stop_event = threading.Event()

        self.publisher = self.create_publisher(Float32MultiArray, "imu_data", qos)
        self.polling_thread = self.polling_function()

    def update(self):
        """Read current Euler angles from the BNO055."""
        euler = self.sensor.euler  # Returns (heading, roll, pitch)
        acc = self.sensor.acceleration  # Returns (x, y, z)
        ang_vel = self.sensor.gyro
        if euler is None or acc is None:
            # Sensor not ready yet
            return

        self.yaw, self.roll, self.pitch = euler
        self.vroll, self.vpitch, self.vyaw = ang_vel
        self.ax, self.ay, self.az = acc

        dt = time.time() - self._last_update_time
        self._last_update_time = time.time()
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        self.vz += self.az * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt

    @threaded
    def polling_function(self):
        while not self.stop_event.is_set():
            self.update()
            self.publisher.publish(
                Float32MultiArray(
                    data=[
                        self.roll,
                        self.pitch,
                        self.yaw,
                        self.vroll,
                        self.vpitch,
                        self.vyaw,
                        self.ax,
                        self.ay,
                        self.az,
                        self.vx,
                        self.vy,
                        self.vz,
                        self.x,
                        self.y,
                        self.z,
                    ]
                )
            )
            if self.stop_event.wait(timeout=1.0 / self.polling_rate):
                break

    def shutdown(self):
        self.get_logger().info("Shutting down IMU tracker")

        self.stop_event.set()

        if self.polling_thread.is_alive():
            self.polling_thread.join(timeout=10)


def main(args=None):
    rclpy.init(args=args)
    print("Starting imu")
    node = IMUTracker(polling_rate=POLLING_RATE)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
