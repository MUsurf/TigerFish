from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    camera_launch = os.path.join(
        get_package_share_directory('cameras'),
        'launch',
        'camera_system.launch.py'
    )

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

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(camera_launch),
            launch_arguments={
                'cam_ids': '0',
                'record_type': 'mp4'
            }.items()
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