#ifndef MOTOR_INTERFACE_HPP
#define MOTOR_INTERFACE_HPP

#include "rclcpp/rclcpp.hpp" //ros2 client library


class MotorListener : public rclcpp::Node
{
    private:
        ///////////////////////////// define all the variables /////////////////////////////////////////
        // Add any private member variables here if needed in the future
        rclcpp::Subscription<std_msgs::msg:Int32MultiArray>::SharedPtr subscription_;

        //smart pointer for MotorInterface Object
        std::unique_ptr<MotorInterface> motor_interface_;

        //thread handler
        std::thread arming_thread_handle_;


        // Motor Configuration //
        const std::vector<int> channels_ = {0, 1, 2, 3, 4, 5, 6, 7}; 
        const size_t num_motors_ = 8;

        // arming thread handle //
        std::thread arming_thread_handle_;

        //////////////////////////// End define all the variables /////////////////////////////////////

        // callback function 
        void motor_callback(const std_msgs::msg::Int32MultiArray::SharedPtr msg);

    public:
        MotorListener();

        ~MotorListener();

        void shutdown();
        // Add any public member functions here if needed in the future


}




#endif // MOTOR_INTERFACE_HPP