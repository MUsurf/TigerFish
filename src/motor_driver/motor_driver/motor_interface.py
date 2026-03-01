from motor_driver.motor_commander import MotorCommander, NUM_MOTORS
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import Float32MultiArray
import time
import rclpy

QOS = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)

FREQ = 40 # hz
LOG_FREQ = 1 # hz
DELTA = 0.75 # per second

ARM_TIME = 2.0

STEP_SIZE = DELTA / FREQ

class MotorInterface(Node):
    def __init__(self):
        super().__init__('motor_interface')
        
        self.motor_commander : MotorCommander = MotorCommander()
        
        self.motor_states = [0.0 for _ in range(NUM_MOTORS)]
        self.motor_goals = [0.0 for _ in range(NUM_MOTORS)]
        
        self.motor_power_subscriber = self.create_subscription(
            Float32MultiArray,
            'motor_powers',
            self.power_cb,
            QOS
        )
        
        self.timer = self.create_timer(1.0 / FREQ, self.timer_cb)
        self.logging_timer = self.create_timer(1.0 / LOG_FREQ, self.log_cb)
        
        self.arm_sequence()
        
    def arm_sequence(self):
        self.set_motor_goals([0.0 for _ in range(NUM_MOTORS)])
        time.sleep(ARM_TIME)
        
    def timer_cb(self):
        self.step_motors()
        
    def log_cb(self):
        self.get_logger().info(f'Motor goals: {self.motor_goals}')
        
    def step_motors(self):
        next_motor_powers = [0.0 for _ in range(NUM_MOTORS)]
        
        for i, (goal, state) in enumerate(zip(self.motor_goals, self.motor_states)):
            distance = goal - state
            if abs(distance) < STEP_SIZE : next_motor_powers[i] = goal
            else : next_motor_powers[i] = state + ((distance > 0) - (distance < 0)) * STEP_SIZE
        
        self.motor_states = next_motor_powers
        self.motor_commander.set_motor_powers(next_motor_powers, 0.025)
            
    def power_cb(self, msg):
        self.set_motor_goals(msg.data)

    def set_motor_goals(self, powers : list) -> bool:
        if len(powers) != NUM_MOTORS : return False
        self.motor_goals = powers
        return True
    
    def stop(self):
        self.motor_goals = [0.0 for _ in range(NUM_MOTORS)]
        self.motor_commander.set_motor_powers([0.0 for _ in range(NUM_MOTORS)])
        self.motor_states = [0.0 for _ in range(NUM_MOTORS)]
        
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