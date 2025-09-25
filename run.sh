#!/bin/bash

source /opt/ros/$ROS_DISTRO/setup.bash
source install/local_setup.bash


ros2 run process_depth depth_node
