"""
VERY IMPORTANT

This will use the NED Frame of Reference

So,
x: forward positive
y: right positive
z: DOWN (NOT UP) positive
roll: right wing down positive
pitch: nose down positive
yaw: right turn positive

BOOOOOMMMM

"""

import rclpy
from rclpy.node import Node
from pid_node.msg import Setpoint, Measurement, Mode
from std_msgs.msg import Float32MultiArray
import math
import numpy as np

from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE)


MIN_X_VELOCITY = 1.5 # m/s?
MIN_Y_VELOCITY = 1.5 # m/s?
MIN_Z_VELOCITY = 1.5 # m/s?
MIN_ROLL_VELOCITY = math.pi / 2 # 90 deg
MIN_PITCH_VELOCITY = math.pi / 2 # 90 deg
MIN_YAW_VELOCITY = math.pi / 2 # 90 deg

FREQUENCY = 200
MAX_POWER = 100.0

class PIDController:
    def __init__(self, kP: float, kI: float, kD: float, integral_max : float = None):
        self.kP : float = kP
        self.kI : float = kI
        self.kD : float = kD
        self.accumulated_error : float = 0.0
        self.last_error : float | None = None
        self.integral_max : float | None = integral_max
        
    def calculate(self, error : float, dt : float) -> float:
        power = self.kP * error
        power += (error - self.last_error) / dt * self.kD if self.last_error is not None else 0.0
        power += self.accumulated_error * self.kI
        self.accumulated_error += error * dt
        if self.integral_max is not None and abs(self.accumulated_error) > abs(self.integral_max):
            if self.accumulated_error < 0 : self.accumulated_error = -abs(self.integral_max)
            else : self.accumulated_error = abs(self.integral_max)
        self.last_error = error
        
        return power
    def __call__(self, error : float, dt : float):
        return self.calculate(error, dt)

class PIDNode(Node):
    def __init__(self,
                 x_kP_pos = 0.05, x_kI_pos = 0.0, x_kD_pos = 0.0, x_kP_vel = 0.05, x_kI_vel = 0.0, x_kD_vel = 0.0,
                 y_kP_pos = 0.05, y_kI_pos = 0.0, y_kD_pos = 0.0, y_kP_vel = 0.05, y_kI_vel = 0.0, y_kD_vel = 0.0,
                 z_kP_pos = 0.05, z_kI_pos = 0.0, z_kD_pos = 0.0, z_kP_vel = 0.05, z_kI_vel = 0.0, z_kD_vel = 0.0,
                 roll_kP_pos = 0.05, roll_kI_pos = 0.0, roll_kD_pos = 0.0, roll_kP_vel = 0.05, roll_kI_vel = 0.0, roll_kD_vel = 0.0,
                 pitch_kP_pos = 0.05, pitch_kI_pos = 0.0, pitch_kD_pos = 0.0, pitch_kP_vel = 0.05, pitch_kI_vel = 0.0, pitch_kD_vel = 0.0,
                 yaw_kP_pos = 0.05, yaw_kI_pos = 0.0, yaw_kD_pos = 0.0, yaw_kP_vel = 0.05, yaw_kI_vel = 0.0, yaw_kD_vel = 0.0,
                 ):
        super().__init__('main')
        self.position_setpoint_subscriber = self.create_subscription(
            Setpoint,
            'position_setpoints',
            self.position_setpoint_cb,
            qos
        )
        self.velocity_setpoint_subscriber = self.create_subscription(
            Setpoint,
            'velocity_setpoints',
            self.velocity_setpoint_cb,
            qos
        )
        self.position_measurement_subscriber = self.create_subscription(
            Setpoint,
            'position_measurements',
            self.position_setpoint_cb,
            qos
        )
        self.velocity_measurement_subscriber = self.create_subscription(
            Setpoint,
            'velocity_measurements',
            self.velocity_setpoint_cb,
            qos
        )
        self.pid_modes = self.create_subscription(
            Mode,
            'pid_modes',
            self.mode_cb,
            qos
        )
        self.motor_publisher = self.create_publisher(
            Float32MultiArray, 
            'motor_powers',
            qos
        )
        
        self.x_pos_controller = PIDController(x_kP_pos, x_kI_pos, x_kD_pos)
        self.x_vel_controller = PIDController(x_kP_vel, x_kI_vel, x_kD_vel)
        
        self.y_pos_controller = PIDController(y_kP_pos, y_kI_pos, y_kD_pos)
        self.y_vel_controller = PIDController(y_kP_vel, y_kI_vel, y_kD_vel)
        
        self.z_pos_controller = PIDController(z_kP_pos, z_kI_pos, z_kD_pos)
        self.z_vel_controller = PIDController(z_kP_vel, z_kI_vel, z_kD_vel)
        
        self.roll_pos_controller = PIDController(roll_kP_pos, roll_kI_pos, roll_kD_pos)
        self.roll_vel_controller = PIDController(roll_kP_vel, roll_kI_vel, roll_kD_vel)
        
        self.pitch_pos_controller = PIDController(pitch_kP_pos, pitch_kI_pos, pitch_kD_pos)
        self.pitch_vel_controller = PIDController(pitch_kP_vel, pitch_kI_vel, pitch_kD_vel)
        
        self.yaw_pos_controller = PIDController(yaw_kP_pos, yaw_kI_pos, yaw_kD_pos)
        self.yaw_vel_controller = PIDController(yaw_kP_vel, yaw_kI_vel, yaw_kD_vel)
        
        self.position_setpoints = Setpoint() # These both SHOULD init to 0
        self.velocity_setpoints = Setpoint()
        
        self.position_measurements = Measurement() # Haven't finished imu yet
        self.velocity_measurements = Measurement() # Haven't finished imu yet
        
        self.modes = Mode()
        
        self.timer = self.create_timer(1.0 / FREQUENCY, self.timer_callback)
        
        self.get_logger().info("PID node started.")
        
        self.mode = 'position'
        
        self.last_time = self.get_clock().now()
        
    def timer_callback(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        self.last_time = now
        
        x_setpoint = self.x_pos_controller(self.position_setpoints.x - self.position_measurements.x, dt) if self.modes.x else self.velocity_setpoints.x
        y_setpoint = self.y_pos_controller(self.position_setpoints.y - self.position_measurements.y, dt) if self.modes.y else self.velocity_setpoints.y
        z_setpoint = self.z_pos_controller(self.position_setpoints.z - self.position_measurements.z, dt) if self.modes.z else self.velocity_setpoints.z
        roll_setpoint = self.roll_pos_controller(self.position_setpoints.roll - self.position_measurements.roll, dt) if self.modes.roll else self.velocity_setpoints.roll
        pitch_setpoint = self.pitch_pos_controller(self.position_setpoints.pitch - self.position_measurements.pitch, dt) if self.modes.pitch else self.velocity_setpoints.pitch
        yaw_setpoint = self.yaw_pos_controller(self.position_setpoints.yaw - self.position_measurements.yaw, dt) if self.modes.yaw else self.velocity_setpoints.yaw
        
        x_pow = self.x_to_motor(self.x_vel_controller(x_setpoint - self.velocity_measurements.x, dt))
        y_pow = self.y_to_motor(self.y_vel_controller(y_setpoint - self.velocity_measurements.y, dt))
        z_pow = self.z_to_motor(self.z_vel_controller(z_setpoint - self.velocity_measurements.z, dt))
        roll_pow = self.roll_to_motor(self.roll_vel_controller(roll_setpoint - self.velocity_measurements.roll, dt))
        pitch_pow = self.pitch_to_motor(self.pitch_vel_controller(pitch_setpoint -self.velocity_measurements.pitch, dt))
        yaw_pow = self.yaw_to_motor(self.yaw_vel_controller(yaw_setpoint - self.velocity_measurements.yaw, dt))
        
        motor_powers = x_pow + y_pow + z_pow + roll_pow + pitch_pow + yaw_pow
        max_pow = np.max(np.abs(motor_powers))
        if max_pow > MAX_POWER:
            motor_powers = (motor_powers / max_pow) * MAX_POWER
            
        message = Float32MultiArray()
        message.data = motor_powers.tolist()
        self.motor_publisher.publish(message)
        
    def x_to_motor(self, x_power) -> np.ndarray:
        return np.array([x_power, x_power, x_power, x_power, 0, 0, 0, 0])
    def y_to_motor(self, y_power) -> np.ndarray:
        return np.array([y_power, -y_power, y_power, -y_power, 0, 0, 0, 0])
    def z_to_motor(self, z_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, -z_power, -z_power, -z_power, -z_power])
    def roll_to_motor(self, roll_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, roll_power, -roll_power, -roll_power, roll_power])
    def pitch_to_motor(self, pitch_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, -pitch_power, -pitch_power, pitch_power, pitch_power])
    def yaw_to_motor(self, yaw_power) -> np.ndarray:
        return np.array([yaw_power, -yaw_power, -yaw_power, yaw_power, 0, 0, 0, 0])
        
    def position_setpoint_cb(self, msg : Setpoint):
        self.position_setpoints = msg
        self.position_updated = True
    def velocity_setpoint_cb(self, msg : Setpoint):
        self.velocity_setpoints = msg
        self.velocity_updated = True
        
    def position_measurement_cb(self, msg : Measurement):
        self.position_measurements = msg
    def velocity_measurement_cb(self, msg : Measurement):
        self.velocity_measurements = msg
    
    def mode_cb(self, msg : Mode):
        self.mode = msg

def main(args=None):
    rclpy.init(args=args)
    node = PIDNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down main node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
