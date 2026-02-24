# Begin imports
from motor_driver.motor_commander import MotorCommand
import time
import threading
import rclpy # pyright: ignore[reportMissingImports]
from rclpy.node import Node # pyright: ignore[reportMissingImports]
from std_msgs.msg import Float32MultiArray # pyright: ignore[reportMissingImports]
# End imports
from rclpy.qos import QoSProfile, ReliabilityPolicy


# Decleration of wrapper for threading a function
def threaded(fn):
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

ARM_TIME = 1.0 # Seconds
CLOSE_TIME = 1.5 # Seconds
DELTA_LIMIT = 0.75 # -1 to 1
UPDATE_FREQUENCY = 20.0 # Hz
LOGGING_FREQUENCY = 5.0 # Hz
NUM_MOTORS = 8 # Number of motors
qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)


class MotorInterface(Node):
    """
    
    """

    def __init__(self) -> None:
        super().__init__('motor_interface')
        self.get_logger().info('Created node')
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'motor_powers',
            self.callback,
            qos
        )
        self.stop_event = threading.Event()
        self.motor_commander : MotorCommand = MotorCommand(UPDATE_FREQUENCY, DELTA_LIMIT)
        self.logger_thread = self.logging_function()
        self.arm_seq()
        

    def arm_seq(self):
        on = [0.25] * NUM_MOTORS
        neutral = [0.0] * NUM_MOTORS
        
        self.motor_commander.pin_targets = neutral
        self.motor_commander.pin_states = neutral
        self.motor_commander.set_motors(neutral)
        time.sleep(ARM_TIME)
        
        # self.motor_commander.pin_targets = on
        # self.motor_commander.pin_states = on
        # self.motor_commander.set_motors(on)
        # time.sleep(ARM_TIME)
        
        # self.motor_commander.pin_targets = neutral
        # self.motor_commander.pin_states = neutral
        # self.motor_commander.set_motors(neutral)
        # time.sleep(ARM_TIME)
        

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""
        
        close_speed = [0.0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_targets(close_speed)
        time.sleep(CLOSE_TIME)
        
    @threaded
    def logging_function(self):
        while not self.stop_event.is_set():
            self.get_logger().info(f"Motor Goals: {self.motor_commander.pin_targets}")
            self.get_logger().info(f"Motor States: {self.motor_commander.pin_states}")
            if self.stop_event.wait(timeout = 1.0 / LOGGING_FREQUENCY):
                break
            
    def callback(self, message_rec : Float32MultiArray):
        """Function that takes in and sets motor powers."""
        
        self.motor_commander.set_targets(message_rec.data)
    
    def shutdown(self):
        try:
            self.get_logger().info("Shutting down motor interface")
        except Exception:
            pass

        # HARD STOP: write neutral PWM immediately, no ROS needed.
        try:
            self.motor_commander.set_motors([0.0] * NUM_MOTORS)
        except Exception:
            pass

        # Ask ramp thread to stop (optional but clean)
        try:
            self.motor_commander.stop_event.set()
        except Exception:
            pass

        self.stop_event.set()

        try:
            if self.logger_thread.is_alive():
                self.logger_thread.join(timeout=1.0)
        except Exception:
            pass

        
def main(args=None):
    rclpy.init(args=args)
    node = MotorInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.shutdown()
        except Exception:
            pass
        try:
            node.destroy_node()
        except Exception:
            pass
        # Guard: launch may already have shut down the context
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass

if __name__ == '__main__':
    main()