from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    args = [
        DeclareLaunchArgument(
            'left_cam_id', default_value='0',
            description='V4L2 device index for the left camera'
        ),
        DeclareLaunchArgument(
            'right_cam_id', default_value='1',
            description='V4L2 device index for the right camera'
        ),
        DeclareLaunchArgument(
            'record_type', default_value='mp4',
            description='Recording format: mp4 or rosbag'
        ),
    ]

    sides = [
        ('camera/left',  LaunchConfiguration('left_cam_id')),
        ('camera/right', LaunchConfiguration('right_cam_id')),
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
