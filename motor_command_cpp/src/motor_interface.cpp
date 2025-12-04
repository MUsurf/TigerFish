#include "motor_command_cpp/motor_interface.hpp"


#include "rclcpp/rclcpp.hpp" //ros2 client library
#include "std_msgs/msg/int32_multi_array.hpp" //ros2 message type
#include "motor_command_cpp/motor_command.hpp" //motor command class


#include <iostream> //input output stream
#include <chrono> //time library
#include <thread> //threading library
#include <atomic> //atomic library for thread safety
#include <memory> //smart pointers
#include <vector> //vector library


    // initialize range 
    void MotorInterface::second_setup()
    {
        this->range = abs(this->max_val - this->offset);
    }

    void MotorInterface::arm_seq()
    {
        // INFO Current method of arming all motors may change with calibration

        std::vector<std::vector<int>> target_speeds = {
            std::vector<int>(this->num_motors, 0)
            //std::vector<int>(this->num_motors, 20),
            //std::vector<int>(this->num_motors, 30),
            //std::vector<int>(this->num_motors, 10)
        };

        // loop through each target speed setting and pin step 
        for (const auto& targets : target_speeds)
        {
            for (int i = 0; i < this->max_steps_needed; ++i)
            {
                this->motor_commander->pinStep(targets);
                std::this_thread::sleep_for(std::chrono::duration<float>(this->minor_time));
            }
        }

        // that that the motors are armed
        RCLCPP_INFO(this->logging_node->get_logger(), "Motors armed");

    }

    void MotorInterface::clo_seq()
    {
        // Cleans up motors and is responsible for bringing them all back to zero

        //initialize a vector of integers to hold the motor targets
        std::vector<int> targets(this->num_motors, 0);

        // loop through each pin and cause them to sleep
        for (int i = 0; i < this->max_steps_needed; ++i)
        {
            this->motor_commander->pinStep(targets);
            std::this_thread::sleep_for(std::chrono::duration<float>(this->minor_time * 10));
        }
    }

    void MotorInterface::run_step()
    {
        if(this->last_directions.empty()) {
            //since the timer handles the period, we don't need to sleep
            return;
        }

        std::vector<int> duty_directions = this->direction_to_motor(this->last_directions);
        std::vector<int> current_states = this->motor_commander->get_pinStates_vec();
        //take a step towards latest target
        this->motor_commander->pinStep(duty_directions);

        bool pin_state_changed = false;
        if(this->motor_commander->get_pinStates_vec() != current_states){
            pin_state_changed = true;

        }

        //log the pin states 
        if (this->logging_node != nullptr && pin_state_changed)
        {
            RCLCPP_INFO(this->logging_node->get_logger(), "Pin states changed: %s", this->motor_commander->pinStates.c_str());
        }

    }

    std::vector<int> MotorInterface::direction_to_motor(const std::vector<float>& directions)
    {
        // This function will have some of the direction to motor commands

        // Notes
        // -----
        //     directions will be in the form of a list of floats
        //         ['x': -1-1, 'y':-1-1, 'z':-1-1, 'pitch':-1-1, 'yaw':-1-1, 'roll':-1-1]
        //     This function is not implemented yet and only contains the translation from percent drive of commands to duty cycle
        // * if you wish to go to the negative end of this axis the magnitude must also be supplied as a negative
        // info For multiple instructions to be followed at once the results post array must be added together while being grouped
        // info This assumes that all motors are number 1-4 5-8 left to right and horizontal then vertical
        // ~ This could be used to balance out an under preforming motor
        std::vector<std::vector<int>> motor_to_directions = {
            {1, 1, -1, -1, 0, 0, 0, 0}, // 'x-axis'
            {1, -1, 1, -1, 0, 0, 0, 0}, // 'y-axis'
            {0, 0, 0, 0, 1, 1, 1, 1}, // 'z-axis' 
            {0, 0, 0, 0, 1, 1, -1, -1}, // 'pitch' 
            {1, -1, -1, 1, 0, 0, 0, 0}, // 'yaw' 
            {0, 0, 0, 0, 1, -1, 1, -1} // 'roll'
            // Add depth control
        };

        // initialize the drive in duty vector to all zeros for the number of motors
        std::vector<int> drive_in_duty(this->num_motors, 0);

        //         # ! Not working need to diagnose later <values being passed are not of type directions but are instead just motor controlls>
        // for index in range(len(directions)):for second_index in  range(len(motor_to_directions[0])):
        //#         drive_in_duty[second_index] += directions[index] * motor_to_directions[index][second_index]
        //# ~ Temp fix for above
        drive_in_duty.clear();
        for(float direction : directions) {
            drive_in_duty.push_back(static_cast<int>(direction));
        }


        //drive_to_duty = [self.__percent_to_duty(duty) for duty in drive_in_duty]

        // for p_direction in directions:
        //  drive_in_duty.append(self.__percent_to_duty(p_direction))
        return (drive_in_duty);


    }

    void MotorInterface::kill_motors()
    {
        // This function will stop the motors and clean up the threads

        // run the closing sequence
        this->clo_seq();

        if (logging_node)
            RCLCPP_INFO(logging_node->get_logger(), "Motors disarmed and interface closed");
    }

    void MotorInterface::callback(const std_msgs::msg::Int32MultiArray::SharedPtr msg)
    {

        // This is set up in a way to allow ros and the motor controls to function on a async basis. This will make sure nothing locks up
        // and that pid gets very low latency feedback (not really but kinda).

        // Function to subscribe to driver with ros
        // This is set up in a way to allow ros and the motor controls to function on a async basis. This will make sure nothing locks up
        // and that pid gets very low latency feedback (not really but kinda).

        std::ostringstream oss;
        for (size_t i = 0; i < msg->data.size(); ++i) {
            oss << msg->data[i];
            if (i != msg->data.size() - 1) oss << ", ";
        }
        RCLCPP_INFO(this->logging_node->get_logger(), "Data received is: [%s]", oss.str().c_str());

        this->last_directions.clear();
        for (int value : msg->data) {
            this->last_directions.push_back(static_cast<float>(value));
        }
        // this->new_directions = true; // Removed unused variable

        // This is still set up in a way that is blocking need to incorporate a major time step to do this
        //         # This is still set up in a way that is blocking need to incorporate a major time step to do this
        //          """ Break down of cases
        //          1) Motors finish getting to targets before next instruction is published 
        //             They should not start running the steping program until new instructions are given
        //          2) Motors finish as new targets arive 
        //             Motors should run with this new information as soon as possible
        //          3) Motors are not finished steping to targets
        //             Motors should finish steping to targets and then start the stepping to the newest target 
        //          """
        // Start the run_step in a new thread if not already running

    }











