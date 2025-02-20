from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='motor_command',
            executable='motor_listener',
            # name='motor_listener',
            # output='screen',
        ),
        Node(
            package='motor_command',
            executable='motor_runner',
            # name='motor_runner',
            # output='screen',
        ),
    ])
