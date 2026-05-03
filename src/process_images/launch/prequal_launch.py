from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='process_images',
            executable='prequal_node',
            name='vision_processor',
            output='screen'
        ),
    ])