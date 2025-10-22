#ifndef MOTOR_INTERFACE_HPP
#define MOTOR_INTERFACE_HPP


#include "rclcpp/rclcpp.hpp" //ros2 client library
#include "std_msgs/msg/int32_multi_array.hpp" //ros2 message type
#include "motor_command.hpp" //motor command class


#include <iostream> //input output stream
#include <chrono> //time library
#include <thread> //threading library
#include <atomic> //atomic library for thread safety
#include <memory> //smart pointers
#include <vector> //vector library
#include <string> //string library


// define the class for the motor interface
class MotorInterface
{
    // This class handles direct control of motors 

    private:
        ///////////////////////////// define all the variables /////////////////////////////////////////
        std::vector<int>                   channels;
        float                              major_time;
        int                                max_val;
        float                              minor_time;
        std::unique_ptr<MotorCommand>      motor_commander;
        int                                num_motors;
        int                                offset;
        int                                range;
        int                                step_size;
        int                                steps_used;
        std::thread                        handle1; // Thread handle for motor control
        int                                max_steps_needed;
        std::vector<float>                 last_directions; // Latest command received from ROS
        std::shared_ptr<std::atomic<bool>> stop_event; // Atomic flag to signal thread to stop
        rclcpp::Node *                     logging_node; // Node for logging
        //////////////////////////// End define all the variables /////////////////////////////////////


        [[deprecated("This function is deprecated as it's functionality has been moved to motor commander")]]
        int percent_to_duty(int percent);


    public:
    MotorInterface(rclcpp::Node * node, std::vector<int> channel, int numMotors, int offset, int max_val, float minor_time, float major_time, int step_size, int steps_used = 10)
        : channels( channel ),
          major_time( major_time ),
          max_val( max_val ),
          minor_time( minor_time ),
          num_motors( numMotors ),
          offset( offset ),
          step_size( step_size ),
          steps_used( steps_used ),
          handle1(),
          stop_event( std::make_shared<std::atomic<bool>>( false ) ),
          logging_node( node )
    {
        // info max steps to go from one extreme to the other
        this->max_steps_needed = (int)(this->max_val / step_size);
        // info this is the instance of motorcommand that will be used
        this->motor_commander = std::make_unique<MotorCommand>( channels, this->num_motors, step_size );
        // INFO this is the latest command received from ros if ros fails to deliver a new value before next execution then the same values are used
        this->last_directions = std::vector<float>();
    }
        ~MotorInterface() { kill_motors(); }

        // initialize range 
        void second_setup();

        std::thread arm_seq();

        void clo_seq();

        void calling_function();

        std::vector<int> direction_to_motor(const std::vector<float>& directions);

        //TODO - this is untested AI code that needs to be tested, but looks useful??
        void kill_motors();

        void callback(const std_msgs::msg::Int32MultiArray::SharedPtr msg);


};


#endif // MOTOR_INTERFACE_HPP




