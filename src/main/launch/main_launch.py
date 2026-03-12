from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='motor_driver',
            executable='motor_interface',
            name='motor_driver'
        ),
        Node(
            package='imu',
            executable='imu_driver',
            name='imu'
        ),
        Node(
            package='depth_sensor',
            executable='depth_sensor_node',
            name='depth_sensor'
        ),
        Node(
            package='process_imu',
            executable='process_imu_node',
            name='process_imu'
        ),
        Node(
            package='state_estimator',
            executable='state_estimator_node',
            name='state_estimator'
        ),
        Node(
            package='cameras',
            executable='camera_publisher',
            name='camera_publisher'
        ),
        Node(
            package='cameras',
            executable='camera_subscriber',
            name='camera_subscriber'
        ),
        Node(
            package='pid',
            executable='pid_node',
            name='pid'
        ),
        Node(
            package='remote_controller',
            executable='remote_controller',
            name='remote_controller'
        ),
        Node(
            package='main',
            executable='main_node',
            name='main'
        ),
    ])
