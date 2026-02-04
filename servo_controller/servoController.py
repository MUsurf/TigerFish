import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

import board
import busio
from adafruit_pca9685 import PCA9685

class ServoController(Node):
    def __init__(self, servo_index):
        super().__init__('servo_controller')
        
        # ~~~ Declare parameters ~~~
         
        self.queue_size = 10
        
        # Name must match publisher node
        self.subscribedTopic='servo_angle'
  
        self.declare_parameter('min_angle', 0.0)
        self.declare_parameter('max_angle', 180.0)
        
        self.declare_parameter('pwm_frequency', 50)
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c)
        
        self.channel = self.pca.channels[servo_index] # PCA has 16 channels (0-15), each servo will use different

        # Servo pulse range (general, might need change for our servo)
        self.declare_parameter('min_duty', 1638)      # 0 degrees
        self.declare_parameter('max_duty', 8192)      # 180 degrees
        
        self.subscription = self.create_subscription(Float32, self.subscribedTopic, self.set_servo_angle, self.queue_size)
                
        self.get_logger().info("Servo controller ready")
        
    def angle_to_duty(self, angle):
        '''Converts angle message to duty cycle'''
        
        # Linearly interpolate angle to get duty cycle
        return int(self.min_duty + (angle / 180.0) * (self.max_duty - self.min_duty))
        
    def set_servo_angle(self, msg):
        '''Callback function, runs every time a message arrives on topic'''    
        
        angle = max(0.0, min(180.0, msg.data)) # Clamp input within our range
        
        self.channel.dity_cycle = self.angle_to_duty(angle) # Convert angle to PWM and sent to I/O
        
        self.get_logger().info(f"Servo angle set to {angle:.1f} degrees")
          
        
def main():
    
    rclpy.init()
    
    # Create node and keep it alive
    node = ServoController()
    rclpy.spin(node)
    
    # Clean up
    node.destroy_node()
    rclpy.shutdown()     
    
           
if __name__ == '__main__':
    
	main()