#include "motor_command_cpp/motor_listener.hpp"

#include "std_msgs/msg/int32_multi_array.hpp" //message type
#include <memory>
#include <thread>
#include <vector>
#include <iostream>

namespace motor_command_cpp
{
  // define constants //
  const float MIN_VAL = 0.0f;
  const float MAX_VAL = 100.0f;
  const float RATE_MIN = 0.1f;
  const float RATE_MAX = 0.5f;
  const int STEP_SIZE = 5;
  const int OFFSET = 1500;
  const float MAJOR_TIME = RATE_MAX;
  const float MINOR_TIME = RATE_MIN;

  // Constructor //
  MotorListener::MotorListener() : Node("motor_listener")
  {

    RCLCPP_INFO(this->get_logger(), "Motor Listener Node started.");

    // intialize motor interface 
    motor_interface_ = std::make_unique<MotorInterface>(
        this, channels_, num_motors_, motor_command_cpp::OFFSET, (int)motor_command_cpp::MAX_VAL, motor_command_cpp::MINOR_TIME, motor_command_cpp::MAJOR_TIME, motor_command_cpp::STEP_SIZE
    );

    // create the subscriber
    subscription_ = this->create_subscription<std_msgs::msg::Int32MultiArray>(
        "motor_commands", rclcpp::QoS(10), std::bind(&MotorListener::motor_callback, this, std::placeholders::_1)
    );
    RCLCPP_INFO(this->get_logger(), "Subscription to 'motor_commands' topic created.");

    // arming
    RCLCPP_INFO(this->get_logger(), "Arming motors...");

    motor_interface_->second_setup();

    auto minor_time_duration = std::chrono::duration<float>(motor_command_cpp::MINOR_TIME);
    motor_control_timer_ = this->create_wall_timer(
        std::chrono::duration_cast<std::chrono::milliseconds>(minor_time_duration),
        std::bind(&MotorListener::motor_control_loop, this)
    );

    RCLCPP_INFO(this->get_logger(), "Motors armed and ready to receive commands.");
  }


  // Destructor //
  MotorListener::~MotorListener()
  {
    // clean up members 
    RCLCPP_INFO(this->get_logger(), "Shutting down Motor Listener Node...");
    this->shutdown();
  }


  // callback function //
  void MotorListener::motor_callback(const std_msgs::msg::Int32MultiArray::SharedPtr msg)
  {
    // log the received message
    std::stringstream ss;
    ss << "Received motor command: [";
    for (size_t i = 0; i < msg->data.size(); ++i) {
      ss << msg->data[i];
      if (i != msg->data.size() - 1) ss << ", ";
    }
    ss << "]";
    RCLCPP_INFO(this->get_logger(), ss.str().c_str());

    // pass the message to the motor interface for processing
    if (motor_interface_) {
      motor_interface_->callback(msg);
    } else {
      RCLCPP_WARN(this->get_logger(), "Motor interface not initialized.");
    }
  }


  // shutdown function //
  void MotorListener::shutdown()
  {
    if(motor_control_timer_){
      motor_control_timer_->cancel();
    }
    motor_interface_->kill_motors();

    //bring motors down to zero
    RCLCPP_INFO(this->get_logger(), "Motors disarmed and interface closed");

  }

  void MotorListener::motor_control_loop()
  {
      // Continuously updates motors toward the latest directions in real time.
      // do this until another thread requests that it stops

      //          3) Motors are not finished steping to targets
      //             Motors should finish steping to targets and then start the stepping to the newest target 
      //          """
      // Start the run_step in a new thread if not already running
      if (motor_interface_){
          motor_interface_->run_step();
      }
  }

} //namespace motor_command_cpp

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  std::cout << "Starting Motor Listener Node..." << std::endl;

  // create the node instance
  auto motor_listener_node = std::make_shared<motor_command_cpp::MotorListener>();


  try{
    rclcpp::spin(motor_listener_node); //spin the node
  } catch (const rclcpp::exceptions::RCLError & e) {
    std::cerr << "RCLError caught: " << e.what() << std::endl;
  } catch (const std::exception & e) {
    std::cerr << "Standard exception caught: " << e.what() << std::endl;
  } catch (...) {
    std::cerr << "Unknown exception caught during rclcpp::spin." << std::endl;
  }
  

  //shutdown sequence 
  motor_listener_node->shutdown();

  motor_listener_node.reset(); // ensure the node is properly destroyed before shutting down ROS 2

  rclcpp::shutdown(); //shutdown ros2

  std::cout << "Node shutdown complete." << std::endl;
  return 0;
}

