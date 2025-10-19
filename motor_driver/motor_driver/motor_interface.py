# Begin imports
from motor_driver.motor_commander import MotorCommand
import time
import threading
import rclpy # pyright: ignore[reportMissingImports]
from rclpy.node import Node # pyright: ignore[reportMissingImports]
from std_msgs.msg import Float32MultiArray # pyright: ignore[reportMissingImports]
# End imports

# Decleration of wrapper for threading a function
def threaded(fn):
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

ARM_TIME = 1.0 # Seconds
CLOSE_TIME = 2.0 # Seconds
DELTA_LIMIT = 75 # Percent
UPDATE_FREQUENCY = 20.0 # Hz
LOGGING_FREQUENCY = 5.0 # Hz
NUM_MOTORS = 8 # Number of motors

class MotorInterface(Node):
    """
    
    """

    def __init__(self) -> None:
        super().__init__('motor_listener')
        self.get_logger().info('Created node')
        self.subscription = self.create_subscription(
            Float32MultiArray,
            'motor_powers',
            self.callback,
            10  # QoS profile depth
        )
        self.stop_event = threading.Event()
        self.motor_commander : MotorCommand = MotorCommand(UPDATE_FREQUENCY, DELTA_LIMIT)
        self.logger_thread = self.logging_function()
        

    def arm_seq(self):
        """Arms the motors (Not technically needed)"""

        arm_speed = [0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_targets(arm_speed)
        time.sleep(ARM_TIME)

        self.logger().info("Motors armed")

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""
        
        close_speed = [0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_targets(close_speed)
        time.sleep(ARM_TIME)
        
    @threaded
    def logging_function(self):
        while not self.stop_event.is_set():
            self.logger().info(f"Motor Goals: {self.motor_commander.logical_pin_targets}")
            self.logger().info(f"Motor States: {self.motor_commander.logical_pin_states}")
            if self.stop_event.wait(timeout = 1.0 / LOGGING_FREQUENCY):
                break
            
    def callback(self, message_rec : Float32MultiArray):
        """Function that takes in and sets motor powers."""
        
        self.motor_commander.set_targets(message_rec.data)
    
    def shutdown(self):
        self.get_logger().info("Shutting down motor listener")
        
        self.clo_seq()
        
        self.stop_event.set()
        self.motor_commander.stop_event.set()
        
        if self.logger_thread.is_alive():
            self.logger_thread.join(timeout=10)
        
def main(args=None):
    rclpy.init(args=args)
    print("Starting listener")
    node = MotorInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()