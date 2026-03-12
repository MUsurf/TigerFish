FROM ros:humble-ros-base

# Set Docker's default shell to bash instead of sh.
SHELL ["/bin/bash", "-c"]

# 1. Install System Dependencies, Build Tools, and YASMIN Web Requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    python3-dev \
    lsb-release \
    gnupg2 \
    python3-pip \
    screen \
    software-properties-common \
    i2c-tools \
    libgpiod-dev \
    python3-libgpiod \
    python3-setuptools \
    python3-colcon-common-extensions \
    ros-humble-cv-bridge \
    ros-humble-vision-opencv \
    # Standard ROS 2 interfaces and build tools
    ros-humble-ament-cmake \
    ros-humble-example-interfaces \
    # RQT and GUI tools for RoboSub debugging
    ros-humble-rqt \
    ros-humble-rqt-common-plugins \
    ros-humble-rqt-graph \
    ros-humble-rqt-image-view \
    ros-humble-rviz2 \
    ros-humble-rviz-default-plugins \
    # Web requirements for yasmin_viewer
    python3-flask \
    python3-flask-cors \
    python3-flask-socketio \
    python3-waitress \
    # Camera calibration packages
    ros-humble-camera-calibration \
    ros-humble-camera-info-manager-py \
    && rm -rf /var/lib/apt/lists/*


# 2. Install hardware-specific Python packages
RUN python3 -m pip install --no-cache \
    adafruit-circuitpython-bno055 \
    adafruit-circuitpython-pca9685==3.4.19 \
    adafruit-blinka==8.66.0 \
    adafruit-python-shell==1.10.0 \
    rpi-lgpio==0.6 \
    #Ruff is a formatter and linter
    ruff \
    expiringdict && \
    python3 -m pip uninstall -y RPi.GPIO 

RUN apt-get update && apt-get install -y \
  lsb-release \
  gnupg2 \
  python3-pip \
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
RUN python3 -m pip install --no-cache gpiozero adafruit-circuitpython-bno055 adafruit-circuitpython-pca9685==3.4.19 adafruit-blinka==8.66.0 adafruit-python-shell==1.10.0 rpi-lgpio==0.6 flask numpy Picamera2 smbus2 && \
  python3 -m pip uninstall -y RPi.GPIO

WORKDIR /home/ros2_ws


# get yasmin if it doesn't already exist
# --- THE YASMIN SYSTEM INSTALL (VERSION 3.4.0) ---
RUN git clone --depth 1 --branch 3.4.0 https://github.com/uleroboticsgroup/yasmin.git /tmp/yasmin && \
    source /opt/ros/humble/setup.bash && \
    cd /tmp/yasmin && \
    colcon build \
    --install-base /opt/ros/humble \
    --merge-install \
    --cmake-args -DCMAKE_BUILD_TYPE=Release && \
    rm -rf /tmp/yasmin

COPY . /home/ros2_ws/

# 3. Rosdep Installation
# RUN --mount=type=bind,source=./process_depth/package.xml,target=/home/ros2_ws/deps/process_depth/package.xml \
#     --mount=type=bind,source=./process_imu/package.xml,target=/home/ros2_ws/deps/process_imu/package.xml \
#     --mount=type=bind,source=./process_images/package.xml,target=/home/ros2_ws/deps/process_images/package.xml \
#     apt-get update && \
#     rosdep update --rosdistro $ROS_DISTRO && \
#     rosdep install -i --from-path /home/ros2_ws/deps --rosdistro $ROS_DISTRO -y && \
#     rm -rf /var/lib/apt/lists/*
RUN --mount=type=bind,source=./src/motor_driver/package.xml,target=/home/ros2_ws/deps/motor_driver/package.xml \
    # --mount=type=bind,source=./src/process_imu/package.xml,target=/home/ros2_ws/deps/process_imu/package.xml \
    # --mount=type=bind,source=./src/state_estimator/package.xml,target=/home/ros2_ws/deps/state_estimator/package.xml \
    --mount=type=bind,source=./src/main/package.xml,target=/home/ros2_ws/deps/main/package.xml \
    --mount=type=bind,source=./src/grabber_servo/package.xml,target=/home/ros2_ws/deps/grabber_servo/package.xml \
    --mount=type=bind,source=./src/process_images/package.xml,target=/home/ros2_ws/deps/process_images/package.xml \
    #--mount=type=bind,source=./src/motor_command/package.xml,target=/home/ros2_ws/deps/motor_command/package.xml \
    apt-get update && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -y --rosdistro humble && \
    rm -rf /var/lib/apt/lists/*


RUN apt-get update && apt-get install -y ros-humble-cv-bridge ros-humble-vision-opencv
# 5. Clean and Build
RUN rm -rf /home/ros2_ws/build /home/ros2_ws/install /home/ros2_ws/log && \
    source /opt/ros/$ROS_DISTRO/setup.bash && \
    colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# 6. Automate Environment Sourcing for the User
# This makes 'ros2' and 'colcon' commands work immediately in new terminals
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /etc/bash.bashrc && \
    echo "source /home/ros2_ws/install/setup.bash" >> /etc/bash.bashrc

# 7. Startup scripts
COPY --chmod=u+x ./run.sh /home/ros2_ws/run.sh

CMD ["bash", "-lc", "mkdir -p /home/ros2_ws/logs && /home/ros2_ws/run.sh > /home/ros2_ws/logs/run.log 2>&1 && tail -f /home/ros2_ws/logs/run.log"]

# CMD ["bash", "-c", "screen -dmS my_session /home/ros2_ws/run.sh && tail -f /dev/null"]