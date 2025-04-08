#!/usr/bin/env python3

'''
ROS 
node: imu_node
Publishes: 
Subscribes:
        - /IMUdata

Maintainer: Luke Deffenbaugh
'''

import rclpy
from sensor_msgs.msg import Imu
from std_msgs.msg import String
import numpy as np

def quaternion_to_euler(x, y, z, w):
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if np.abs(sinp) >= 1:
        pitch = np.sign(sinp) * (np.pi / 2)  # Use 90 degrees if out of range
    else:
        pitch = np.arcsin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw

class imuData:
    def __init__(self, data):
        '''
        Hold the data in specific formats

        Orientation: Held in Euler format
            0 : Roll
            1 : Pitch
            2 : Yaw

        Angular Velocity: < Need to determine what its unit is >
            0 : X
            1 : Y
            2 : Z

        Linear Acceleration: < Need to determine what its unit is >
            0 : X
            1 : Y     
            2 : Z   
        '''

        # Transform the data into Roll Pitch and Yaw
        euler = quaternion_to_euler(data.orientation.x, data.orientation.y, data.orientation.z, data.orientation.w)

        # Store the data into tuples
        self.orientation = (euler[0], euler[1], euler[2])
        self.angular_velocity = (data.angular_velocity.x, data.angular_velocity.y, data.angular_velocity.z)
        self.linear_acceleration = (data.linear_acceleration.x, data.linear_acceleration.y, data.linear_acceleration.z)

    def __repr__(self):
        return (f"Orientation: {self.orientation[0]} {self.orientation[1]} {self.orientation[2]}\n"
                f"Angular_Velocity: {self.angular_velocity[0]} {self.angular_velocity[1]} {self.angular_velocity[2]}\n"
                f"Linear_Acceleration: {self.linear_acceleration[0]} {self.linear_acceleration[1]} {self.linear_acceleration[2]}\n")




def imu_callback(data):
    '''
    # IMU Callback Function #
    This is the code that is called each time the subscriber receives data from the subscribed topic
    '''

    # Initialize Object
    imudata = imuData(data)

    # Publish a string of the __repr__ function output
    imu_string_publisher.publish(str(imudata))

def imu_node():
    ''' 
    Create and handle ROS environment setup.
    '''

    # Setup Node
    node = rclpy.create_node("imu_node")
    # Setup Subscriber
    node.create_subscription(Imu, "imu_data", imu_callback, 10)

    # Create a publisher
    global imu_string_publisher
    imu_string_publisher = node.create_publisher(String, "processed_imu", 10)


    # Keep the node running
    rclpy.spin(node)


############ Main #############
if __name__ == '__main__':
    try:
        # Run the node
        rclpy.init()
        imu_node()
    except rclpy.exceptions.ROSInterruptException:
        # Handle a ros interruption
        pass
    # Add special case handlers here