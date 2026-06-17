from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    args = [
        DeclareLaunchArgument(
            'front_left_camera_id', default_value='0',
            description='V4L2 device index for the left camera'
        ),
        DeclareLaunchArgument(
            'front_right_camera_id', default_value='4',
            description='V4L2 device index for the right camera'
        ),
        DeclareLaunchArgument(
            'bottom_left_camera_id', default_value='1',
            description='V4L2 device index for the left camera'
        ),
        DeclareLaunchArgument(
            'bottom_right_camera_id', default_value='3',
            description='V4L2 device index for the right camera'
        ),
        DeclareLaunchArgument(
            'record_type', default_value='mp4',
            description='Recording format: mp4 or rosbag'
        ),
    ]

    sides = [
        ('front_left_camera',  LaunchConfiguration('front_left_camera_id')),
        ('front_right_camera', LaunchConfiguration('front_right_camera_id')),
    ]

    nodes = []
    for ns, cam_id in sides:
        nodes.append(Node(
            package='cameras',
            executable='camera_publisher',
            namespace=ns,
            parameters=[{'camera_index': cam_id}],
            output='screen',
        ))
        nodes.append(Node(
            package='cameras',
            executable='subscriber_node',
            namespace=ns,
            parameters=[{'record_type': LaunchConfiguration('record_type')}],
            output='screen',
        ))

    return LaunchDescription(args + nodes)
