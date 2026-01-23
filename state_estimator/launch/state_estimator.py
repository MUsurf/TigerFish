from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="state_estimator",
                executable="state_estimator_launch",
                # name='motor_runner',
                # output='screen',
            )
        ]
    )
