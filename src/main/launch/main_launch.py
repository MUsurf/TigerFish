from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='imu',
            executable='imu_driver',
            name='imu'
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
            package='main',
            executable='main_node',
            name='main'
        ),
    ])
