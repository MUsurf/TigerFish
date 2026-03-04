from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, Float32, String, Bool # pyright: ignore[reportMissingImports]
from messages.msg import PIDInput, ControllerInput

import rclpy
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
import numpy as np


qos = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT
)

kill_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

new_controller_qos = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE
)

qos_controller = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)

YAW_DEGREE_PER_SECOND = 10
Z_METER_PER_SECOND = 0.5
DEAD_ZONE = 0.1

def new_controller_str(text : str) -> Float32MultiArray:
    parts = text.split(":")

    if len(parts) != 4:
        return None

    axis = parts[0]
    
    axis = str(axis).lower()
    
    if axis == 'x':
        axis = 0.0
    elif axis == 'y':
        axis = 1.0
    elif axis == 'z':
        axis = 2.0
    elif axis in ['roll', 'r']:
        axis = 3.0
    elif axis == ['pitch', 'p']:
        axis = 4.0
    elif axis == ['yaw', 'y']:
        axis = 5.0
    else:
        return None

    try:
        v1 = float(parts[1])
        v2 = float(parts[2])
        v3 = float(parts[3])
    except ValueError:
        None
        
    msg = Float32MultiArray()
    msg.data = [axis, v1, v2, v3]
    return msg


def rpy_from_quat(q):
    """
    Convert geometry_msgs.msg.Quaternion to roll, pitch, yaw (radians).
    
    Assumes quaternion fields:
        q.x, q.y, q.z, q.w
    Uses XYZ (roll, pitch, yaw) convention.
    """

    x = q.x
    y = q.y
    z = q.z
    w = q.w

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = np.sign(sinp) * (np.pi / 2.0)  # use 90° if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        
        self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self._odom_cb, 10)
        
        # self.motor_publisher = self.create_publisher(
        #     Float32MultiArray,
        #     "motor_powers",
        #     qos
        # )
        
        self.command_line_subscriber = self.create_subscription(
            String,
            'command_line',
            self.command_line_cb,
            qos_controller
        )
        
        self.controller_subscriber = self.create_subscription(
            ControllerInput,
            "controller_input",
            self.controller_cb,
            qos_controller
        )
        
        self.depth_sensor_subscriber = self.create_subscription(
            Float32,
            'depth',
            self.depth_sensor_cb,
            10
        )
        
        self.pid_publisher = self.create_publisher(
            PIDInput,
            "pid_input",
            10
        )
        
        self.new_controller_publisher = self.create_publisher(
            Float32MultiArray,
            'new_pid_controller',
            new_controller_qos
        )
        
        self.kill_publisher = self.create_publisher(
            Bool,
            "kill",
            kill_qos
        )
        
        period = 1.0 / 10.0
        self.timer = self.create_timer(period, self._timer_cb)
        self.start_time = time.time()
        self.switch_time = 2
        
        self.recent_controller_input : ControllerInput = None
        
        self.x_pow : float = 0.0
        self.y_pow : float = 0.0
        
        self.z_setpoint : float = 0.0
        self.roll_setpoint : float = 0.0
        self.pitch_setpoint : float = 0.0
        self.yaw_setpoint : float = 0.0
        
        self.depth : float = 0.0
        self.roll : float = 0.0
        self.pitch : float = 0.0
        self.yaw : float = 0.0
        
        self.controller_last_time = None
        
    def depth_sensor_cb(self, msg : Float32):
        self.get_logger().info(f'{msg.data}')
        
    def _timer_cb(self):
        msg = PIDInput()
        
        msg.x_mode = False
        msg.y_mode = False
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        
        msg.x_power = 0 if self.recent_controller_input is None else self.recent_controller_input.x_left_stick
        msg.y_power = 0.0

        msg.z_setpoint = self.z_setpoint
        msg.z_measurement = max(0.0, self.depth)
        
        msg.roll_setpoint = 0.0
        msg.roll_measurement = self.roll * 180 / np.pi
        msg.pitch_setpoint = 0.0
        msg.pitch_setpoint = self.pitch * 180 / np.pi
        msg.yaw_setpoint = 0.0
        msg.yaw_measurement = self.yaw * 180 / np.pi
        
        self.pid_publisher.publish(msg)
        
    def command_line_cb(self, msg : String):
        text = msg.data.strip()
        
        if text == 'kill' or text == 'k':
            msg = Bool()
            msg.data = True
            self.kill_publisher.publish(msg)

        is_pid = new_controller_str(text)
        if is_pid is not None : self.new_controller_publisher.publish(is_pid)
        
    def controller_cb(self, msg : ControllerInput):
        if abs(msg.x_left_stick) < DEAD_ZONE : msg.x_left_stick = 0.0
        if abs(msg.y_left_stick) < DEAD_ZONE : msg.y_left_stick = 0.0
        if abs(msg.y_right_stick) < DEAD_ZONE : msg.y_right_stick = 0.0
        if abs(msg.r_trigger) < DEAD_ZONE : msg.r_trigger = 0.0
        if abs(msg.l_trigger) < DEAD_ZONE : msg.l_trigger = 0.0
        
        self.recent_controller_input = msg
        self.x_power = msg.y_left_stick
        self.y_power = msg.x_left_stick
        
        if self.controller_last_time is None:
            self.controller_last_time = time.time()
            return
        dt = time.time() - self.controller_last_time
        self.controller_last_time = time.time()
        
        yaw_power = max(msg.r_trigger, msg.l_trigger)
        yaw_power *= -1 if msg.l_trigger > msg.r_trigger else 1
        self.yaw_setpoint += YAW_DEGREE_PER_SECOND * yaw_power * dt
        
        z_set = Z_METER_PER_SECOND * msg.y_right_stick * dt
        self.z_setpoint += z_set
        
        # self.get_logger().info(f'{self.recent_controller_input.x_left_stick}')
        
    def _odom_cb(self, msg : Odometry):
        r, p, y = rpy_from_quat(msg.pose.pose.orientation)
        self.roll = -r
        self.pitch = -p
        self.yaw = - y
        self.get_logger().info(f'roll: {(r * 180 / np.pi):4f} pitch {(p * 180 / np.pi):4f} yaw: {(y * 180 / np.pi):4f}')
        # msg = PIDInput()
        
        # msg.x_mode = False
        # msg.y_mode = False
        # msg.z_mode = False
        # msg.roll_mode = True
        # msg.pitch_mode = True
        # msg.yaw_mode = True
        
        # msg.x_power = 0 if self.recent_controller_input is None else self.recent_controller_input.x_left_stick
        # msg.y_power = 0.0
        # msg.z_power = 0.0
        
        # msg.roll_setpoint = 0.0
        # msg.roll_measurement = r * 180 / np.pi
        # msg.pitch_setpoint = 0.0
        # msg.pitch_setpoint = p * 180 / np.pi
        # msg.yaw_setpoint = 0.0
        # msg.yaw_measurement = y * 180 / np.pi
        
        # self.pid_publisher.publish(msg)
        
        
def main(args=None):
    rclpy.init(args=args)
    node = MainNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()