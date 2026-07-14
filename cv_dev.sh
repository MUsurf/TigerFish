#!/bin/bash
# CV development helper — builds camera + vision packages, starts camera
# publishers, then runs the vision pipeline or single-camera calibration.
#
# Usage:
#   ./cv_dev.sh                              # vision mode, fed by cameras (default)
#   ./cv_dev.sh calibrate                    # calibrate LEFT camera, fed by cameras (needs X11)
#   ./cv_dev.sh calibrate right              # calibrate RIGHT camera, fed by cameras (needs X11)
#   ./cv_dev.sh video                        # vision mode, fed by video files instead of cameras
#   ./cv_dev.sh calibrate video              # calibrate LEFT camera, fed by video file (needs X11)
#   ./cv_dev.sh calibrate right video        # calibrate RIGHT camera, fed by video file (needs X11)
#   ./cv_dev.sh calibrate image              # calibrate LEFT camera from image directory (needs X11)
#   ./cv_dev.sh calibrate right image        # calibrate RIGHT camera from image directory (needs X11)
#   ./cv_dev.sh mono                         # mono_calibration_node on LEFT video (needs X11)
#   ./cv_dev.sh mono right                   # mono_calibration_node on RIGHT video (needs X11)
#
# Camera indices default to 0=left, 1=right. Override if needed:
#   LEFT_CAM=1 RIGHT_CAM=0 ./cv_dev.sh
#
# Video files default to test_videos/High-res-left.mp4 and High-res-right.mp4.
# Override if needed:
#   LEFT_VIDEO_PATH=/path/left.mp4 RIGHT_VIDEO_PATH=/path/right.mp4 ./cv_dev.sh video
#
# Image directories default to test_images/left and test_images/right.
# Override if needed:
#   LEFT_IMAGE_DIR=/path/to/imgs RIGHT_IMAGE_DIR=/path/to/imgs ./cv_dev.sh calibrate image

set -e

WORKSPACE=/home/ros2_ws
LEFT_CAM=${LEFT_CAM:-0}
RIGHT_CAM=${RIGHT_CAM:-1}
LEFT_VIDEO_PATH=${LEFT_VIDEO_PATH:-/home/ros2_ws/test_videos/High-res-left.mp4}
RIGHT_VIDEO_PATH=${RIGHT_VIDEO_PATH:-/home/ros2_ws/test_videos/High-res-right.mp4}
LEFT_IMAGE_DIR=${LEFT_IMAGE_DIR:-/home/ros2_ws/test_images/left}
RIGHT_IMAGE_DIR=${RIGHT_IMAGE_DIR:-/home/ros2_ws/test_images/right}

MODE=vision
SOURCE=camera
SIDE=left
for arg in "$@"; do
    case "$arg" in
        calibrate)    MODE=calibrate ;;
        vision)       MODE=vision ;;
        mono)         MODE=mono ;;
        video)        SOURCE=video ;;
        image)        SOURCE=image ;;
        camera)       SOURCE=camera ;;
        left)         SIDE=left ;;
        right)        SIDE=right ;;
        *)
            echo "ERROR: unknown argument '$arg' (expected: vision, calibrate, mono, left, right, video, camera, image)"
            exit 1
            ;;
    esac
done

if [ "$SOURCE" = "image" ] && [ "$MODE" != "calibrate" ]; then
    echo "ERROR: 'image' source is only valid in calibrate mode"
    exit 1
fi

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

if [ "$MODE" = "mono" ]; then
    if [ "$SIDE" = "left" ]; then
        VIDEO_PATH="$LEFT_VIDEO_PATH"
    else
        VIDEO_PATH="$RIGHT_VIDEO_PATH"
    fi
    if [ ! -f "$VIDEO_PATH" ]; then
        echo "ERROR: video file not found at $VIDEO_PATH"
        echo "       Drop a .mp4 into ./test_videos/ or set LEFT_VIDEO_PATH/RIGHT_VIDEO_PATH"
        exit 1
    fi
    if [ "$BOARD" = "aruco" ]; then USE_ARUCO=true; else USE_ARUCO=false; fi
    echo "==> Starting mono_calibration_node ($SIDE: $VIDEO_PATH, board=$BOARD)..."
    echo "    SPACE=capture  C=calibrate+save  B=toggle board  Q/ESC=quit"
    ros2 run process_images mono_calibration_node --ros-args \
        -p video_path:="$VIDEO_PATH" \
        -p square_size:=0.030 \
        -p use_aruco_board:=$USE_ARUCO \
        -p output_file:=src/src/process_images/config/mono_calibration.yaml
    exit 0
fi

if [ "$SOURCE" = "image" ]; then
    if [ "$SIDE" = "left" ]; then
        IMAGE_DIR="$LEFT_IMAGE_DIR"
    else
        IMAGE_DIR="$RIGHT_IMAGE_DIR"
    fi
    if [ ! -d "$IMAGE_DIR" ]; then
        echo "ERROR: image directory not found at $IMAGE_DIR"
        echo "       Create it and drop jpg/png files inside, or set LEFT_IMAGE_DIR / RIGHT_IMAGE_DIR"
        exit 1
    fi
    echo "==> Image mode — loading from $IMAGE_DIR (no publisher needed)"
    echo "==> Starting calibration node ($SIDE camera — N/P=navigate  SPACE=capture  C=calibrate)..."
    ros2 run process_images stereo_calibration_node --ros-args \
        -p image_dir:="$IMAGE_DIR" \
        -p square_size:=0.030 \
        -p output_file:=config/${SIDE}_calibration.yaml
    exit 0
elif [ "$SOURCE" = "video" ]; then
    if [ "$MODE" = "calibrate" ]; then
        # Single-camera calibration: only start the selected side's video
        if [ "$SIDE" = "left" ]; then
            VIDEO_PATH="$LEFT_VIDEO_PATH"
        else
            VIDEO_PATH="$RIGHT_VIDEO_PATH"
        fi
        if [ ! -f "$VIDEO_PATH" ]; then
            echo "ERROR: video file not found at $VIDEO_PATH"
            exit 1
        fi
        echo "==> Starting video_pub_node ($SIDE: $VIDEO_PATH)..."
        ros2 run process_images video_pub_node --ros-args \
            -p video_path:="$VIDEO_PATH" \
            -r camera/image_raw:=camera/$SIDE/image_raw &
    else
        if [ ! -f "$LEFT_VIDEO_PATH" ]; then
            echo "ERROR: left video file not found at $LEFT_VIDEO_PATH"
            echo "       Drop a .mp4 into ./test_videos/ or set LEFT_VIDEO_PATH=/path/to/file.mp4"
            exit 1
        fi
        if [ ! -f "$RIGHT_VIDEO_PATH" ]; then
            echo "ERROR: right video file not found at $RIGHT_VIDEO_PATH"
            echo "       Drop a .mp4 into ./test_videos/ or set RIGHT_VIDEO_PATH=/path/to/file.mp4"
            exit 1
        fi
        echo "==> Starting video_pub_node (left: $LEFT_VIDEO_PATH, right: $RIGHT_VIDEO_PATH)..."
        ros2 run process_images video_pub_node --ros-args \
            -p video_path:="$LEFT_VIDEO_PATH" \
            -r camera/image_raw:=camera/left/image_raw &
        ros2 run process_images video_pub_node --ros-args \
            -p video_path:="$RIGHT_VIDEO_PATH" \
            -r camera/image_raw:=camera/right/image_raw &
    fi
else
    if [ "$MODE" = "calibrate" ]; then
        # Single-camera calibration: only start the selected side's camera
        if [ "$SIDE" = "left" ]; then
            CAM_IDX=$LEFT_CAM
        else
            CAM_IDX=$RIGHT_CAM
        fi
        echo "==> Starting camera publisher ($SIDE=cam$CAM_IDX)..."
        ros2 run cameras camera_publisher --ros-args \
            -r __ns:=/camera/$SIDE \
            -p camera_index:=$CAM_IDX &
    else
        echo "==> Starting stereo camera publishers (left=cam$LEFT_CAM, right=cam$RIGHT_CAM)..."
        ros2 run cameras camera_publisher --ros-args \
            -r __ns:=/camera/left \
            -p camera_index:=$LEFT_CAM &
        ros2 run cameras camera_publisher --ros-args \
            -r __ns:=/camera/right \
            -p camera_index:=$RIGHT_CAM &
    fi
fi

# brief pause so camera nodes are ready before the consumer starts
sleep 1

if [ "$MODE" = "calibrate" ]; then
    echo "==> Starting calibration node ($SIDE camera — press SPACE to capture, C to calibrate)..."
    ros2 run process_images stereo_calibration_node --ros-args \
        -p camera_topic:=camera/$SIDE/image_raw \
        -p square_size:=0.030 \
        -p output_file:=config/${SIDE}_calibration.yaml
else
    echo "==> Starting vision pipeline..."
    ros2 run process_images process_img &

    echo "==> Opening debug image viewer (markers/debug_image)..."
    ros2 run image_view image_view --ros-args -r image:=markers/debug_image
fi
