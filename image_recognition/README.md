# Image Recognition Package Documentation

## Overview

The `image_recognition` package is a ROS 2 package designed to detect and process orange oblong shapes, find the contours, and publish the key points (start, middle, and end 2D coordinates) of the shape.

## Features

- Digestion of a `/image_topic` to accept images
- Convex hull analysis to find key points on detected shapes
- Publication of detected points as ROS 2 messages
- Includes a test image publisher for testing

## Package Structure

```
image_recognition/
├── image_recognition/
│   ├── __init__.py
│   ├── image_detection_script.py  # Main detection algorithm
│   └── image_publisher.py         # Test image publisher
├── test_images/                   # Test images for development
│   └── mask.png                   # Sample test image
├── setup.py                       # Package setup configuration
└── package.xml                    # Package metadata
```

## Dependencies

- ROS 2 (tested on Humble)
- OpenCV (cv2)
- NumPy
- cv_bridge
- Standard ROS 2 message types:
  - sensor_msgs
  - geometry_msgs
  - std_msgs

## Installation

### Prerequisites

Ensure you have ROS 2 installed and your workspace set up.

### Building the Package

1. Clone this package into your ROS 2 workspace's `src` directory:
   ```bash
   cd ~/ros2_ws/src
   git clone https://github.com/MUsurf/ImageRecognition/ --branch packageAttempt
   mv ImageRecognition/ image_recognition
   ```

2. Build the package:
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select image_recognition
   ```

3. Source the workspace:
   ```bash
   source ~/ros2_ws/install/setup.bash
   ```

## Usage

The package provides two main nodes:

### 1. Image Detection Node (`line_detector`)

This node subscribes to camera images and processes them to detect orange objects, analyze their contours, and publish key points.

```bash
ros2 run image_recognition line_detector
```

#### Subscribed Topics
- `image_topic` ([sensor_msgs/Image](http://docs.ros.org/en/api/sensor_msgs/html/msg/Image.html)): Input camera image

#### Published Topics
- `positions` ([geometry_msgs/PoseArray](http://docs.ros.org/en/api/geometry_msgs/html/msg/PoseArray.html)): Array of three poses representing the start, middle, and end points of the detected shape

### 2. Test Image Publisher Node (`image_publisher`)

This node publishes test images for development and testing purposes.

```bash
ros2 run image_recognition image_publisher
```

#### Published Topics
- `/image_topic` ([sensor_msgs/Image](http://docs.ros.org/en/api/sensor_msgs/html/msg/Image.html)): Test image published at 10 times a second

## Algorithm Details

The image detection algorithm follows these steps:

1. Convert the input image from BGR to HSV color space
2. Apply color thresholding to isolate orange objects (HSV range: [0, 150, 150] to [30, 255, 255])
3. Apply morphological operations to smooth the detected mask
4. Find contours in the mask
5. For the largest contour:
   - Calculate the convex hull
   - Find convexity defects
   - Identify the most significant defect point (with maximum distance)
   - Extract the start, middle (defect), and end points
6. Publish these three points as a PoseArray message

## API Reference

### `imageDetectionPkg` Class

Main class for image processing and detection.

#### Methods

- `__init__()`: Initializes the node, creates publishers and subscribers
- `imageDetection(msg)`: Callback function for processing incoming images
  - **Parameters**: 
    - `msg` ([sensor_msgs/Image](http://docs.ros.org/en/api/sensor_msgs/html/msg/Image.html)): Input image message

### `ImagePublisher` Class

Node class for publishing test images.

#### Methods

- `__init__()`: Initializes the node, creates publishers and timers
- `publish_image()`: Function to publish the test image periodically

## Configuration

The image detection parameters can be modified in the `image_detection_script.py` file near the top:

- Publisher/Subscription node names:
  ```python
  POSE_ARRAY_PUBLISHER = 'positions' # string
  IMAGE_SUBSCRIPTION = 'image_topic' # string
  ```

- HSV color range for object detection:
  ```python
  LOWER_COLOR = np.array([0, 150, 150]) # HSV np array
  UPPER_COLOR = np.array([30, 255, 255]) # HSV np array
  ```

- Morphological kernel size:
  ```python
  MORPH_KERNEL = np.ones((15, 15), np.uint8) # np matrix
  ```


## Troubleshooting

- If no objects are detected, try adjusting the HSV color threshold values to match your specific orange object.
- Check camera image quality and lighting conditions for better detection.

## Future Improvements

- Addition of dynamic parameter configuration
- Improved visualization options for debugging
- Better publisher options

## More Thorough Installation

```sh
cd /home/ros2_ws/src
git clone https://github.com/MUsurf/ImageRecognition/ --branch packageAttempt
mv ImageRecognition/ image_recognition

apt update
apt install python3-opencv
apt install ros-${ROS_DISTRO}-cv-bridge # Add to docker on build 

source /opt/ros/$ROS_DISTRO/setup.bash # Add to docker on build
source /home/ros2_ws/install/local_setup.bash

colcon build --packages-select image_recognition --symlink-install # Symlink is to avoid future caching issues

source install/setup.bash
ros2 run image_recognition line_detector
# ros2 run image_recognition image_publisher
```