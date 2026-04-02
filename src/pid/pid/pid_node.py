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
from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Odometry
import numpy as np
from messages.msg import PIDInput
import time

from rclpy.qos import QoSProfile, ReliabilityPolicy

motor_qos = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.BEST_EFFORT
)

new_controller_qos = QoSProfile(
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE
)

FREQ = 25 # Hz

class PIDController:
    def __init__(self, kP: float, kI: float, kD: float, integral_max : float = None):
        self.kP : float = kP
        self.kI : float = kI
        self.kD : float = kD
        self.accumulated_error : float = 0.0
        self.last_error : float | None = None
        self.integral_max : float | None = integral_max
        
    def calculate(self, error : float, dt : float) -> float:
        self.accumulated_error += error * dt
        if self.integral_max is not None and abs(self.accumulated_error) > abs(self.integral_max):
            if self.accumulated_error < 0 : self.accumulated_error = -abs(self.integral_max)
            else : self.accumulated_error = abs(self.integral_max)
        power = self.kP * error
        power += (error - self.last_error) / dt * self.kD if self.last_error is not None else 0.0
        power += self.accumulated_error * self.kI
        
        self.last_error = error
        
        return power
    def __call__(self, error : float, dt : float):
        return self.calculate(error, dt)
    
def rotate_vector_by_quat(v, q):
    x, y, z, w = q
    q_vec = np.array([x, y, z])
    
    t = 2.0 * np.cross(q_vec, v)
    v_prime = v + w * t + np.cross(q_vec, t)
    return v_prime


class PIDNode(Node):
    def __init__(self,
             x_gains=(0.1, 0.0, 0.0),
             y_gains=(0.1, 0.0, 0.0),
             z_gains=(0.1, 0.0, 0.0),
             roll_gains=(0.01, 0.0, 0.0),
             pitch_gains=(0.01, 0.0, 0.0),
             yaw_gains=(0.01, 0.0, 0.0)):
        super().__init__('pid_node')
        self.x_kP, self.x_kI, self.x_kD = x_gains
        self.y_kP, self.y_kI, self.y_kD = y_gains
        self.z_kP, self.z_kI, self.z_kD = z_gains
        self.roll_kP, self.roll_kI, self.roll_kD = roll_gains
        self.pitch_kP, self.pitch_kI, self.pitch_kD = pitch_gains
        self.yaw_kP, self.yaw_kI, self.yaw_kD = yaw_gains
        
        self.x_pid = PIDController(self.x_kP, self.x_kI, self.x_kD)
        self.y_pid = PIDController(self.y_kP, self.y_kI, self.y_kD)
        self.z_pid = PIDController(self.z_kP, self.z_kI, self.z_kD)

        self.roll_pid = PIDController(self.roll_kP, self.roll_kI, self.roll_kD)
        self.pitch_pid = PIDController(self.pitch_kP, self.pitch_kI, self.pitch_kD)
        self.yaw_pid = PIDController(self.yaw_kP, self.yaw_kI, self.yaw_kD)
        
        self.last_time = self.get_clock().now()
        
        self.pid_input_subscriber = self.create_subscription(
            PIDInput,
            'pid_input',
            self.input_cb,
            10
        )
        
        self.new_pid_subscriber = self.create_subscription(
            Float32MultiArray,
            'new_pid_controller',
            self.new_controller_cb,
            new_controller_qos
        )
        
        self.motor_publisher = self.create_publisher(
            Float32MultiArray,
            'motor_powers',
            motor_qos
        )
        
        self.orientation_subscriber = self.create_subscription(Odometry, 'state_estimation', self.odom_cb, 10)
        self.last_od : Odometry = None
        
        self.last_msg = PIDInput()
        
        period = 1.0 / FREQ
        self.timer = self.create_timer(period, self.timer_cb)
        
        self.locked = False
        
        self.get_logger().info("PID node created")
        
    def timer_cb(self):
        if not self.last_od : return
        if not self.last_msg : return

        
        if self.locked:
            return
        self.locked = True
        
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds * 1e-9
        dt = max(1e-4, min(dt, 0.2))
        self.last_time = now
        
        x_pow = self.last_msg.x_power if not self.last_msg.x_mode \
            else self.x_pid(self.last_msg.x_setpoint - self.last_msg.x_measurement, dt)

        y_pow = self.last_msg.y_power if not self.last_msg.y_mode \
            else self.y_pid(self.last_msg.y_setpoint - self.last_msg.y_measurement, dt)

        z_pow = self.last_msg.z_power if not self.last_msg.z_mode \
            else self.z_pid(self.last_msg.z_setpoint - self.last_msg.z_measurement, dt)

        roll_pow = self.last_msg.roll_power if not self.last_msg.roll_mode \
            else self.roll_pid(self.last_msg.roll_setpoint - self.last_msg.roll_measurement, dt)

        pitch_pow = self.last_msg.pitch_power if not self.last_msg.pitch_mode \
            else self.pitch_pid(self.last_msg.pitch_setpoint - self.last_msg.pitch_measurement, dt)

        yaw_pow = self.last_msg.yaw_power if not self.last_msg.yaw_mode \
            else self.yaw_pid(self.last_msg.yaw_setpoint - self.last_msg.yaw_measurement, dt)
            
            
        q = self.last_od.pose.pose.orientation
        q = (q.x, q.y, q.z, q.w)
        if not self.last_msg.x_is_absolute: 
            x_pow = self.x_to_motor(x_pow)
        else: 
            v = np.array([x_pow,0,0])
            v = rotate_vector_by_quat(v, q)
            x_comp = self.x_to_motor(v[0])
            y_comp = self.y_to_motor(v[1])
            z_comp = self.z_to_motor(v[2])
            x_pow = x_comp + y_comp + z_comp
        
        if not self.last_msg.y_is_absolute: 
            y_pow = self.y_to_motor(y_pow)
        else:
            v = np.array([0,y_pow,0])
            v = rotate_vector_by_quat(v, q)
            x_comp = self.x_to_motor(v[0])
            y_comp = self.y_to_motor(v[1])
            z_comp = self.z_to_motor(v[2])
            y_pow = x_comp + y_comp + z_comp
        
        
        if not self.last_msg.z_is_absolute: 
            z_pow = self.z_to_motor(z_pow)
        else:
            v = np.array([0,0,z_pow])
            v = rotate_vector_by_quat(v, q)
            x_comp = self.x_to_motor(v[0])
            y_comp = self.y_to_motor(v[1])
            z_comp = self.z_to_motor(v[2])
            z_pow = x_comp + y_comp + z_comp
        
        
        roll_pow = self.roll_to_motor(roll_pow)
        pitch_pow = self.pitch_to_motor(pitch_pow)
        yaw_pow = self.yaw_to_motor(yaw_pow)
        
        motor_powers = x_pow + y_pow + z_pow + roll_pow + pitch_pow + yaw_pow
        
        motor_powers[4:8] *= 0.707 # adjust the z to reflect how we lose some of our power on the x and y axis
        
        m = np.max(np.abs(motor_powers))
        if m > 1.0:
            motor_powers = motor_powers / m
        
        motor_powers[4:8] = motor_powers[4:8] * -1
            
        message = Float32MultiArray()
        message.data = motor_powers.tolist()
        self.motor_publisher.publish(message)
        
        self.locked = False
        
    def new_controller_cb(self, msg : Float32MultiArray):
        while self.locked:
            time.sleep(0.0005)
        self.locked = True
        
        msg = msg.data
        if msg[0] < 0.5 : self.x_pid = PIDController(msg[1], msg[2], msg[3])
        elif msg[0] < 1.5 : self.y_pid = PIDController(msg[1], msg[2], msg[3])
        elif msg[0] < 2.5 : self.z_pid = PIDController(msg[1], msg[2], msg[3])
        elif msg[0] < 3.5 : self.roll_pid = PIDController(msg[1], msg[2], msg[3])
        elif msg[0] < 4.5 : self.pitch_pid = PIDController(msg[1], msg[2], msg[3])
        elif msg[0] < 5.5 : self.yaw_pid = PIDController(msg[1], msg[2], msg[3])
            
        self.locked = False
        
    def odom_cb(self, msg : Odometry):
        self.last_od = msg
        
    def x_to_motor(self, x_power) -> np.ndarray:
        return np.array([x_power, x_power, x_power, x_power, 0, 0, 0, 0])
    def y_to_motor(self, y_power) -> np.ndarray:
        return np.array([y_power, -y_power, y_power, -y_power, 0, 0, 0, 0])
    def z_to_motor(self, z_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, z_power, z_power, - z_power, - z_power])
    def roll_to_motor(self, roll_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, -roll_power, roll_power, roll_power, -roll_power])
    def pitch_to_motor(self, pitch_power) -> np.ndarray:
        return np.array([0, 0, 0, 0, pitch_power, pitch_power, -pitch_power, -pitch_power])
    def yaw_to_motor(self, yaw_power) -> np.ndarray:
        return np.array([yaw_power, -yaw_power, -yaw_power, yaw_power, 0, 0, 0, 0])
        
    def input_cb(self, msg : PIDInput):
        self.last_msg = msg
        

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
