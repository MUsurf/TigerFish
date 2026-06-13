"""
Main vision pipeline launch file.

Default mode uses the video file publisher (both cameras point to the same
test topic). For real deployment set use_test_video:=false and configure
your stereo camera driver to publish on camera/left/image_raw and
camera/right/image_raw.

Examples
--------
# Test with video file (default):
ros2 launch process_images tigerfish_vision.launch.py

# Live stereo cameras:
ros2 launch process_images tigerfish_vision.launch.py use_test_video:=false

# Save debug video:
ros2 launch process_images tigerfish_vision.launch.py \
    output_video_path:=/tmp/debug.mp4
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('process_images')
    default_cal = os.path.join(pkg_share, 'config', 'stereo_calibration.yaml')

    args = [
        DeclareLaunchArgument('use_test_video', default_value='true',
                              description='Launch video_pub_node for testing'),
        DeclareLaunchArgument('left_camera_topic',
                              default_value='camera/image_raw',
                              description='Left camera image topic'),
        DeclareLaunchArgument('right_camera_topic',
                              default_value='camera/image_raw',
                              description='Right camera image topic (same as left for single-file test)'),
        DeclareLaunchArgument('stereo_calibration_file',
                              default_value=default_cal,
                              description='Path to stereo_calibration.yaml'),
        DeclareLaunchArgument('marker_actual_width', default_value='1.2',
                              description='Physical marker width in meters'),
        DeclareLaunchArgument('marker_min_area', default_value='600.0',
                              description='Minimum contour area in pixels'),
        DeclareLaunchArgument('hsv_h_low',  default_value='8'),
        DeclareLaunchArgument('hsv_h_high', default_value='22'),
        DeclareLaunchArgument('hsv_s_low',  default_value='110'),
        DeclareLaunchArgument('hsv_s_high', default_value='255'),
        DeclareLaunchArgument('hsv_v_low',  default_value='80'),
        DeclareLaunchArgument('hsv_v_high', default_value='255'),
        DeclareLaunchArgument('output_video_path', default_value='',
                              description='Write debug video here (empty = disabled)'),
    ]

    video_pub = Node(
        package='process_images',
        executable='video_pub_node',
        name='video_pub_node',
        condition=IfCondition(LaunchConfiguration('use_test_video')),
    )

    process_img = Node(
        package='process_images',
        executable='process_img',
        name='process_img_node',
        parameters=[{
            'stereo_calibration_file': LaunchConfiguration('stereo_calibration_file'),
            'marker_actual_width':     LaunchConfiguration('marker_actual_width'),
            'left_camera_topic':       LaunchConfiguration('left_camera_topic'),
            'right_camera_topic':      LaunchConfiguration('right_camera_topic'),
            'marker_min_area':         LaunchConfiguration('marker_min_area'),
            'hsv_h_low':               LaunchConfiguration('hsv_h_low'),
            'hsv_h_high':              LaunchConfiguration('hsv_h_high'),
            'hsv_s_low':               LaunchConfiguration('hsv_s_low'),
            'hsv_s_high':              LaunchConfiguration('hsv_s_high'),
            'hsv_v_low':               LaunchConfiguration('hsv_v_low'),
            'hsv_v_high':              LaunchConfiguration('hsv_v_high'),
            'output_video_path':       LaunchConfiguration('output_video_path'),
        }],
    )

    return LaunchDescription(args + [video_pub, process_img])
