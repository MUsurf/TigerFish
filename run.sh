#!/bin/bash

source /opt/ros/$ROS_DISTRO/setup.bash && \
  source install/local_setup.bash && \
  exec ros2 launch main main_launch.py
