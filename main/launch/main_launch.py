from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="main",
                executable="main_launch",
                # name='motor_runner',
                # output='screen',
            )
        ]
    )
