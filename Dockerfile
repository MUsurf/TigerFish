FROM ros:jazzy-ros-base


SHELL ["/bin/bash", "-c"]

# 1. Install System Dependencies, Build Tools, and YASMIN Web Requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
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
    # Standard ROS 2 interfaces and build tools
    ros-jazzy-ament-cmake \
    ros-jazzy-example-interfaces \
    # RQT and GUI tools for RoboSub debugging
    ros-jazzy-rqt \
    ros-jazzy-rqt-common-plugins \
    ros-jazzy-rqt-graph \
    ros-jazzy-rqt-image-view \
    ros-jazzy-rviz2 \
    ros-jazzy-rviz-default-plugins \
    ros-jazzy-rosidl-default-generators \
    # Web requirements for yasmin_viewer
    python3-flask \
    python3-flask-cors \
    python3-flask-socketio \
    python3-waitress \
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
    expiringdict \
    --break-system-packages && \
    python3 -m pip uninstall -y RPi.GPIO --break-system-packages

WORKDIR /home/ros2_ws
RUN mkdir -p /home/ros2_ws/deps

# get yasmin if it doesn't already exist
ARG YASMIN_VERSION=3.4.0
RUN if [ ! -d "/home/ros2_ws/src/yasmin" ]; then \
        git clone https://github.com/uleroboticsgroup/yasmin.git /home/ros2_ws/src/yasmin; \
        echo "Successfully cloned YASMIN 3.4.0 - ROS JAZZY"; \
    else \
        echo "YASMIN already detected in src, skipping YASMIN clone."; \
    fi


# 3. Rosdep Installation
RUN --mount=type=bind,source=./process_depth/package.xml,target=/home/ros2_ws/deps/process_depth/package.xml \
    --mount=type=bind,source=./process_imu/package.xml,target=/home/ros2_ws/deps/process_imu/package.xml \
    --mount=type=bind,source=./process_images/package.xml,target=/home/ros2_ws/deps/process_images/package.xml \
    apt-get update && \
    rosdep update --rosdistro $ROS_DISTRO && \
    rosdep install -i --from-path /home/ros2_ws/deps --rosdistro $ROS_DISTRO -y && \
    rm -rf /var/lib/apt/lists/*

# 4. Copy source code
COPY ./ /home/ros2_ws/src/

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

# CMD ["bash", "-c", "screen -dmS my_session /home/ros2_ws/run.sh && tail -f /dev/null"]