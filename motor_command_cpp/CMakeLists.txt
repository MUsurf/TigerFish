cmake_minimum_required(VERSION 3.10)
project(motor_command_cpp)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

#####################################################
# Setup Libraries 
#####################################################
add_library(${PROJECT_NAME}_lib
  src/motor_interface.cpp
)

target_include_directories(${PROJECT_NAME}_lib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${rclcpp_INCLUDE_DIRS} # Include directories of rclcpp
  ${std_msgs_INCLUDE_DIRS} # Include directories of std_msgs
)

target_link_libraries(${PROJECT_NAME}_lib
  rclcpp::rclcpp
  ${std_msgs_LIBRARIES}
)

#####################################################
# Executable targets
#####################################################

add_executable(motor_runner src/motor_runner.cpp)
ament_target_dependencies(motor_runner rclcpp)
target_link_libraries(motor_runner ${PROJECT_NAME}_lib)
target_include_directories(motor_runner PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_executable(motor_listener src/motor_listener.cpp)
ament_target_dependencies(motor_listener rclcpp std_msgs)
target_link_libraries(motor_listener ${PROJECT_NAME}_lib)
target_include_directories(motor_listener PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)


install(DIRECTORY include/
  DESTINATION include
)

install(TARGETS ${PROJECT_NAME}_lib
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
)

install(TARGETS
  motor_runner
  motor_listener
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)




#####################################################
# Testing & Export
#####################################################
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
