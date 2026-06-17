from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    camera_launch = os.path.join(
        get_package_share_directory('cameras'),
        'launch',
        'camera_system.launch.py'
    )
    vision_launch = os.path.join(
        get_package_share_directory('process_images'),
        'launch',
        'tigerfish_vision.launch.py'
    )

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

    return LaunchDescription(args + [
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
        # Node(
        #     package='python_cv',
        #     executable='gate_yolo',
        #     name='gate_yolo'
        # ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(camera_launch),
            launch_arguments={
                'front_left_camera_id':  LaunchConfiguration('front_left_camera_id'),
                'front_right_camera_id': LaunchConfiguration('front_right_camera_id'),
                'record_type':  LaunchConfiguration('record_type'),
            }.items()
        ),
    ])
