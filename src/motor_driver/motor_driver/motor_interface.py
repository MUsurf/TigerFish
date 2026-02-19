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
CLOSE_TIME = 0.1 # Seconds
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
        

    def arm_seq(self):
        """Arms the motors (Not technically needed)"""

        arm_speed = [0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_targets(arm_speed)
        time.sleep(ARM_TIME)

        self.get_logger().info("Motors armed")

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""
        
        close_speed = [0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_targets(close_speed)
        time.sleep(CLOSE_TIME)
        
    @threaded
    def logging_function(self):
        while not self.stop_event.is_set():
            # self.get_logger().info(f"Motor Goals: {self.motor_commander.logical_pin_targets}")
            # self.get_logger().info(f"Motor States: {self.motor_commander.logical_pin_states}")
            if self.stop_event.wait(timeout = 1.0 / LOGGING_FREQUENCY):
                break
            
    def callback(self, message_rec : Float32MultiArray):
        """Function that takes in and sets motor powers."""
        
        self.motor_commander.set_targets(message_rec.data)
    
    def shutdown(self):
        self.get_logger().info("Shutting down motor interface")
        
        self.clo_seq()
        
        self.stop_event.set()
        # self.motor_commander.stop_event.set()
        
        if self.logger_thread.is_alive():
            self.logger_thread.join(timeout=10)
        # if self.motor_commander.motor_thread.is_alive():
        #     self.motor_commander.motor_thread.join(timeout=10)
        
def main(args=None):
    rclpy.init(args=args)
    print("Starting interface")
    node = MotorInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.motor_commander.stop()
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()