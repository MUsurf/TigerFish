cmake_minimum_required(VERSION 3.8)
project(process_images)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(OpenCV REQUIRED)

include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
)

# ── process_img ────────────────────────────────────────────────────────────────
# Main vision node: stereo marker detection + publisher
add_executable(process_img
  src/process_img_node.cpp
  src/img_preprocessing.cpp
  src/marker_detector.cpp
  src/gate_detection.cpp
)
target_include_directories(process_img PRIVATE include ${OpenCV_INCLUDE_DIRS})
ament_target_dependencies(process_img
  rclcpp sensor_msgs geometry_msgs cv_bridge image_transport)
target_link_libraries(process_img ${OpenCV_LIBRARIES})

# ── stereo_calibration_node ────────────────────────────────────────────────────
# Interactive stereo calibration; saves config/stereo_calibration.yaml
add_executable(stereo_calibration_node
  src/stereo_calibration_node.cpp
)
target_include_directories(stereo_calibration_node PRIVATE include ${OpenCV_INCLUDE_DIRS})
ament_target_dependencies(stereo_calibration_node
  rclcpp sensor_msgs cv_bridge)
target_link_libraries(stereo_calibration_node ${OpenCV_LIBRARIES})

# ── video_pub_node ─────────────────────────────────────────────────────────────
# Test helper: publishes an MP4 file as camera/image_raw
add_executable(video_pub_node
  src/video_publisher.cpp
)
target_include_directories(video_pub_node PRIVATE include ${OpenCV_INCLUDE_DIRS})
ament_target_dependencies(video_pub_node rclcpp sensor_msgs cv_bridge)
target_link_libraries(video_pub_node ${OpenCV_LIBRARIES})

# ── Install ────────────────────────────────────────────────────────────────────
install(TARGETS
  process_img
  stereo_calibration_node
  video_pub_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# ── Tests ──────────────────────────────────────────────────────────────────────
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
