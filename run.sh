#!/bin/bash

source /opt/ros/$ROS_DISTRO/setup.bash && \
  source install/local_setup.bash && \
  ros2 launch main main_launch.py
