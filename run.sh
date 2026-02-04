#!/bin/bash

source /opt/ros/$ROS_DISTRO/setup.bash && \
  source install/local_setup.bash && \
  # python3 ./src/Helpers/i2c_find.py
  # python3 ./src/motor_command/motor_command/motor_listener.py
  ros2 launch main main_launch.py