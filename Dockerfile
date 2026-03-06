FROM ros:humble-ros-base

# Set Docker's default shell to bash instead of sh.
SHELL ["/bin/bash", "-c"]


RUN apt-get update && apt-get install -y \
  lsb-release \
  gnupg2 \
  python3-pip \
  python3-opencv \
  libcap-dev \
  screen \
  software-properties-common \
  i2c-tools \
  libgpiod-dev \
  python3-libgpiod \
  libgpiod-doc \
  ros-humble-camera-calibration \
  ros-humble-camera-info-manager-py \
  python3-setuptools && \
  rm -rf /var/lib/apt/lists/* && \
  apt-get clean

# Install packages not availble through system
RUN python3 -m pip install --no-cache gpiozero adafruit-circuitpython-bno055 adafruit-circuitpython-pca9685==3.4.19 adafruit-blinka==8.66.0 adafruit-python-shell==1.10.0 rpi-lgpio==0.6 flask numpy Picamera2 cv_bridge smbus2 && \
  python3 -m pip uninstall -y RPi.GPIO

WORKDIR /home/ros2_ws

# Initialize rosdep and install dependencies for all packages.
# We are using bind mounts here to optimize build times.
# Make sure you follow this syntax: "--mount=type=bind,source=./<your_new_package>/package.xml,target=/home/ros2_ws/deps/<your_new_package>/package.xml \"
# Bind mounts are whitespace sensitive. You can copy and paste the given syntax and replace <your_new_package> with the name of the package you want to add.
RUN \
    --mount=type=bind,source=./src/motor_driver/package.xml,target=/home/ros2_ws/deps/motor_driver/package.xml \
    # --mount=type=bind,source=./src/process_imu/package.xml,target=/home/ros2_ws/deps/process_imu/package.xml \
    # --mount=type=bind,source=./src/state_estimator/package.xml,target=/home/ros2_ws/deps/state_estimator/package.xml \
    --mount=type=bind,source=./src/main/package.xml,target=/home/ros2_ws/deps/main/package.xml \
    --mount=type=bind,source=./src/grabber_servo/package.xml,target=/home/ros2_ws/deps/grabber_servo/package.xml \
    #--mount=type=bind,source=./src/motor_command/package.xml,target=/home/ros2_ws/deps/motor_command/package.xml \

    rosdep update && \
    rosdep install -i --from-path ./deps --rosdistro $ROS_DISTRO -y

COPY ./ /home/ros2_ws/src/

RUN source /opt/ros/$ROS_DISTRO/setup.bash && \
  colcon build --symlink-install

# run.sh is where we run commands in the container on startup.
COPY --chmod=u+x ./run.sh /home/ros2_ws/run.sh

CMD ["bash", "-lc", "mkdir -p /home/ros2_ws/logs && /home/ros2_ws/run.sh > /home/ros2_ws/logs/run.log 2>&1 && tail -f /home/ros2_ws/logs/run.log"]
