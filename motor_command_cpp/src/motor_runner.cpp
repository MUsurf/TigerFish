#include "rclcpp/rclcpp.hpp"
#include "motor_command_cpp/motor_interface.hpp" // Include your library header

// NOTE THAT THIS FILE IS A PLACEHOLDER AND DOES NOT IMPLEMENT ANY FUNCTIONALITY
// IT IS ONLY HERE TO ALLOW THE PROJECT TO COMPILE SUCCESSFULLY
int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  
  // Create a base node for the MotorInterface to use for logging/context
  auto node = std::make_shared<rclcpp::Node>("motor_runner_node");
  
  // Instantiate your MotorInterface (You'll need to pass proper arguments here)
  // Since we don't know the exact arguments, we'll use placeholders for now:
  std::vector<int> channels = {0, 1, 2, 3};
  int numMotors = 4;
  int offset = 0;
  int max_val = 1000;
  float minor_time = 0.001f;
  float major_time = 0.1f;
  int step_size = 10;
  
  auto interface = std::make_shared<MotorInterface>(
      node, channels, numMotors, offset, max_val, minor_time, major_time, step_size
  );
  
  interface->second_setup();
  interface->arm_seq(); // Start the motor thread

  RCLCPP_INFO(node->get_logger(), "Motor Runner Node started.");

  // Spin the executor to allow ROS 2 to process timers, topics, etc.
  rclcpp::spin(node); 
  
  // Clean up
  interface->kill_motors();
  rclcpp::shutdown();
  return 0;
}