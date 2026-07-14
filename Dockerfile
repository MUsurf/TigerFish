# L4T JetPack 6.0 (Orin Nano) base — ships CUDA/cuDNN/TensorRT for the Jetson's
# GPU. Must match the JetPack version flashed on the device (r36.3.0 = JetPack 6.0).
FROM nvcr.io/nvidia/l4t-jetpack:r36.3.0

# Set Docker's default shell to bash instead of sh.
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

ARG TORCH_WHEEL

# 0. Install ROS 2 Humble — the l4t-jetpack base doesn't ship it like ros:humble-ros-base did.
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    curl \
    gnupg2 \
    lsb-release \
    software-properties-common \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && add-apt-repository universe \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
       -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo ${UBUNTU_CODENAME}) main" \
       > /etc/apt/sources.list.d/ros2.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       ros-humble-ros-base \
       python3-rosdep \
       python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init || true

# 1. Install System Dependencies, Build Tools
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
    # Camera calibration packages
    ros-humble-camera-calibration \
    ros-humble-camera-info-manager-py \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade "packaging>=22"

# 2. Install hardware-specific Python packages
RUN python3 -m pip install --no-cache \
    adafruit-circuitpython-bno055 \
    adafruit-circuitpython-pca9685==3.4.19 \
    adafruit-blinka==8.66.0 \
    adafruit-python-shell==1.10.0 \
    rpi-lgpio==0.6 \
    ruff \
    expiringdict && \
    python3 -m pip uninstall -y RPi.GPIO 

RUN apt-get update && apt-get install -y \
  lsb-release \
  gnupg2 \
  python3-pip \
  libcap-dev \
  screen \
  ros-humble-cv-bridge \
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

RUN python3 -m pip install \
    --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio \
    && python3 -m pip install --no-deps ultralytics


# Install packages not availble through system
RUN python3 -m pip install gpiozero adafruit-circuitpython-bno055 adafruit-circuitpython-pca9685==3.4.19 adafruit-blinka==8.66.0 adafruit-python-shell==1.10.0 rpi-lgpio==0.6 flask "numpy<2" smbus2 opencv-python Jetson.GPIO && \
  python3 -m pip uninstall -y RPi.GPIO


  
WORKDIR /home/ros2_ws


# get yasmin if it doesn't already exist
# --- THE YASMIN SYSTEM INSTALL (VERSION 3.4.0) ---
# RUN git clone --depth 1 --branch 3.4.0 https://github.com/uleroboticsgroup/yasmin.git /tmp/yasmin && \
#     source /opt/ros/humble/setup.bash && \
#     cd /tmp/yasmin && \
#     colcon build \
#     --install-base /opt/ros/humble \
#     --merge-install \
#     --cmake-args -DCMAKE_BUILD_TYPE=Release && \
#     rm -rf /tmp/yasmin

# Better yasmin install
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-yasmin \
    ros-humble-yasmin-ros \
    ros-humble-yasmin-msgs \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=./src/cameras/package.xml,target=/home/ros2_ws/deps/cameras/package.xml \
    --mount=type=bind,source=./src/depth_sensor/package.xml,target=/home/ros2_ws/deps/depth_sensor/package.xml \
    --mount=type=bind,source=./src/grabber_servo/package.xml,target=/home/ros2_ws/deps/grabber_servo/package.xml \
    --mount=type=bind,source=./src/imu/package.xml,target=/home/ros2_ws/deps/imu/package.xml \
    --mount=type=bind,source=./src/main/package.xml,target=/home/ros2_ws/deps/main/package.xml \
    --mount=type=bind,source=./src/messages/package.xml,target=/home/ros2_ws/deps/messages/package.xml \
    --mount=type=bind,source=./src/motor_driver/package.xml,target=/home/ros2_ws/deps/motor_driver/package.xml \
    --mount=type=bind,source=./src/pid/package.xml,target=/home/ros2_ws/deps/pid/package.xml \
    --mount=type=bind,source=./src/process_cameras/package.xml,target=/home/ros2_ws/deps/process_cameras/package.xml \
    --mount=type=bind,source=./src/process_images/package.xml,target=/home/ros2_ws/deps/process_images/package.xml \
    --mount=type=bind,source=./src/process_imu/package.xml,target=/home/ros2_ws/deps/process_imu/package.xml \
    --mount=type=bind,source=./src/remote_controller/package.xml,target=/home/ros2_ws/deps/remote_controller/package.xml \
    --mount=type=bind,source=./src/state_estimator/package.xml,target=/home/ros2_ws/deps/state_estimator/package.xml \
    --mount=type=bind,source=./src/state_machine/package.xml,target=/home/ros2_ws/deps/state_machine/package.xml \

    apt-get update && \
    rosdep update && \
    rosdep install -i --from-path ./deps --rosdistro $ROS_DISTRO -y

COPY ./ /home/ros2_ws/src/
COPY ./makefile /home/ros2_ws/makefile

RUN source /opt/ros/$ROS_DISTRO/setup.bash && \
    colcon build --symlink-install --parallel-workers 4

RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc && \
    echo "source /your_ws/install/setup.bash" >> /root/.bashrc

# 6. Automate Environment Sourcing for the User
# This makes 'ros2' and 'colcon' commands work immediately in new terminals
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /etc/bash.bashrc && \
    echo "source /home/ros2_ws/install/setup.bash" >> /etc/bash.bashrc

# 7. Startup scripts
COPY --chmod=u+x ./run.sh /home/ros2_ws/run.sh

# CMD ["bash", "-lc", "mkdir -p /home/ros2_ws/logs && /home/ros2_ws/run.sh > /home/ros2_ws/logs/run.log 2>&1 && tail -f /home/ros2_ws/logs/run.log"]
# This version ensures you see the errors in your 'make up' terminal
CMD ["/bin/bash", "-c", "source /opt/ros/humble/setup.bash && source /home/ros2_ws/install/setup.bash && /home/ros2_ws/run.sh"]