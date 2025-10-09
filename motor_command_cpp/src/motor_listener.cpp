#include "rclcpp/rclcpp.hpp"

// NOTE THAT THIS FILE IS A PLACEHOLDER AND DOES NOT IMPLEMENT ANY FUNCTIONALITY
// IT IS ONLY HERE TO ALLOW THE PROJECT TO COMPILE SUCCESSFULLY
int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("motor_listener_node");
  
  RCLCPP_INFO(node->get_logger(), "Motor Listener Node started.");
  
  // The logic for listening to a topic would go here, 
  // or a simple while(rclcpp::ok()) loop if it's just meant to run.
  
  rclcpp::spin(node); 
  rclcpp::shutdown();
  return 0;
}