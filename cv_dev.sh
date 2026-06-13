#!/bin/bash
# CV development helper — builds camera + vision packages, starts stereo camera
# publishers, then runs the vision pipeline or stereo calibration.
#
# Usage:
#   ./cv_dev.sh              # vision mode (default)
#   ./cv_dev.sh calibrate    # stereo calibration mode (needs X11)
#   ./cv_dev.sh video        # vision mode fed by video_pub_node instead of cameras
#
# Camera indices default to 0=left, 1=right. Override if needed:
#   LEFT_CAM=1 RIGHT_CAM=0 ./cv_dev.sh

set -e

WORKSPACE=/home/ros2_ws
MODE=${1:-vision}
LEFT_CAM=${LEFT_CAM:-0}
RIGHT_CAM=${RIGHT_CAM:-1}
VIDEO_PATH=${VIDEO_PATH:-/home/ros2_ws/test_videos/test.mp4}

cd "$WORKSPACE"

echo "==> Building packages..."
colcon build --packages-select cameras process_images --symlink-install
source install/setup.bash

cleanup() {
    echo ""
    echo "==> Shutting down..."
    # kill all background jobs spawned by this script
    jobs -p | xargs -r kill 2>/dev/null
    wait 2>/dev/null
}
trap cleanup EXIT INT TERM

if [ "$MODE" = "video" ]; then
    if [ ! -f "$VIDEO_PATH" ]; then
        echo "ERROR: video file not found at $VIDEO_PATH"
        echo "       Drop a .mp4 into ./test_videos/ or set VIDEO_PATH=/path/to/file.mp4"
        exit 1
    fi
    echo "==> Starting video_pub_node (source: $VIDEO_PATH)..."
    ros2 run process_images video_pub_node --ros-args \
        -p video_path:="$VIDEO_PATH" \
        -r camera/image_raw:=camera/left/image_raw &
    ros2 run process_images video_pub_node --ros-args \
        -p video_path:="$VIDEO_PATH" \
        -r camera/image_raw:=camera/right/image_raw &
else
    echo "==> Starting stereo camera publishers (left=cam$LEFT_CAM, right=cam$RIGHT_CAM)..."
    ros2 run cameras camera_publisher --ros-args \
        -r __ns:=/camera/left \
        -p camera_index:=$LEFT_CAM &
    ros2 run cameras camera_publisher --ros-args \
        -r __ns:=/camera/right \
        -p camera_index:=$RIGHT_CAM &
fi

# brief pause so camera nodes are ready before the consumer starts
sleep 1

if [ "$MODE" = "calibrate" ]; then
    echo "==> Starting stereo calibration node (press SPACE to capture, C to calibrate)..."
    ros2 run process_images stereo_calibration_node --ros-args \
        -p square_size:=0.025 \
        -p output_file:=config/stereo_calibration.yaml
else
    echo "==> Starting vision pipeline..."
    ros2 run process_images process_img &

    echo "==> Opening debug image viewer (markers/debug_image)..."
    ros2 run image_view image_view --ros-args -r image:=markers/debug_image
fi
