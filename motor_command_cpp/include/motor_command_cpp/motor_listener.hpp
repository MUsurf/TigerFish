#ifndef MOTOR_LISTENER_HPP
#define MOTOR_LISTENER_HPP

#include "rclcpp/rclcpp.hpp" //ros2 client library
#include "motor_command_cpp/motor_interface.hpp"
#include "std_msgs/msg/int32_multi_array.hpp"

namespace motor_command_cpp
{

  // define the MotorListener class //
    class MotorListener : public rclcpp::Node
    {
        private:
            ///////////////////////////// define all the variables /////////////////////////////////////////
            rclcpp::Subscription<std_msgs::msg::Int32MultiArray>::SharedPtr subscription_;

            
            //smart pointer for MotorInterface Object
            std::unique_ptr<MotorInterface> motor_interface_;

            rclcpp::TimerBase::SharedPtr motor_control_timer_;

            // Motor Configuration //
            const std::vector<int> channels_ = {0, 1, 2, 3, 4, 5, 6, 7}; 
            const size_t num_motors_ = 8;

            //////////////////////////// End define all the variables /////////////////////////////////////

            // callback function 
            void motor_callback(const std_msgs::msg::Int32MultiArray::SharedPtr msg);

            void motor_control_loop();

        public:
            MotorListener();

            ~MotorListener();

            void shutdown();
            // Add any public member functions here if needed in the future


    };
} //namespace motor_command_cpp




#endif // MOTOR_LISTENER_HPP