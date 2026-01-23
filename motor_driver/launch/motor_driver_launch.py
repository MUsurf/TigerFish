from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="motor_driver",
                executable="motor_interface",
                # name='motor_runner',
                # output='screen',
            )
        ]
    )
