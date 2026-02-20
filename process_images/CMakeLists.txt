cmake_minimum_required(VERSION 3.8)
project(process_images)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(OpenCV REQUIRED)
find_package(tiger_fish_msgs REQUIRED)

include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
)

# executable
add_executable(process_img
  src/process_img_node.cpp
  src/img_preprocessing.cpp
  src/marker_detector.cpp
)

add_executable(video_pub_node
  src/video_publisher.cpp
)

# link libraries
ament_target_dependencies(process_img rclcpp sensor_msgs cv_bridge OpenCV tiger_fish_msgs)
ament_target_dependencies(video_pub_node rclcpp sensor_msgs cv_bridge OpenCV)

install(TARGETS 
  process_img
  video_pub_node
  DESTINATION lib/${PROJECT_NAME}
)

# make the compiler more intense!
#add_compile_options(-Wall -Wextra -Wpedantic)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
