"""
Stereo calibration session launch file.

Before running:
  1. Measure one square of printed checkerboard with a ruler.
  2. Pass that measurement (in meters) as square_size.
  3. Confirm board_width and board_height match your checkerboard's inner corners.

Example (9x6 board, 25 mm squares):
  ros2 launch process_images stereo_calibration.launch.py \
      square_size:=0.025

The node opens an OpenCV window showing both camera feeds.
  SPACE  — capture a corner pair (hold board still, corners visible in both cameras)
  C      — run calibration and save once min_captures pairs are collected
  Q/ESC  — quit without saving
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('process_images')
    default_output = os.path.join(pkg_share, 'config', 'stereo_calibration.yaml')

    args = [
        DeclareLaunchArgument('left_camera_topic',
                              default_value='camera/left/image_raw'),
        DeclareLaunchArgument('right_camera_topic',
                              default_value='camera/right/image_raw'),
        DeclareLaunchArgument('board_width',  default_value='9',
                              description='Number of inner corners along width'),
        DeclareLaunchArgument('board_height', default_value='6',
                              description='Number of inner corners along height'),
        DeclareLaunchArgument('square_size',  default_value='0.025',
                              description='Physical square side length in meters — MEASURE THIS'),
        DeclareLaunchArgument('min_captures', default_value='20',
                              description='Minimum valid pairs before calibration is allowed'),
        DeclareLaunchArgument('output_file',  default_value=default_output,
                              description='Where to save the calibration YAML'),
    ]

    cal_node = Node(
        package='process_images',
        executable='stereo_calibration_node',
        name='stereo_calibration_node',
        parameters=[{
            'left_camera_topic':  LaunchConfiguration('left_camera_topic'),
            'right_camera_topic': LaunchConfiguration('right_camera_topic'),
            'board_width':        LaunchConfiguration('board_width'),
            'board_height':       LaunchConfiguration('board_height'),
            'square_size':        LaunchConfiguration('square_size'),
            'min_captures':       LaunchConfiguration('min_captures'),
            'output_file':        LaunchConfiguration('output_file'),
        }],
        output='screen',
    )

    return LaunchDescription(args + [cal_node])
