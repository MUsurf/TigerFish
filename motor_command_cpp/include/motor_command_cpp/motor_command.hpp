#ifndef MOTOR_COMMAND_HPP
#define MOTOR_COMMAND_HPP

#include <vector>
#include <string>
#include "pca_driver.hpp" 
#include <sstream> // For std::stringstream
#include <cstdint> // For uint8_t


class MotorCommand
{
    private: 
        //////////////////////// Variables //////////////////////////
        
        size_t              motorNum; // Number of motors being managed
        int                 step_size; // How much to move the motors at each minor step


        // PCA9685 Driver instance
        PWMDriver           pca; 


        // Channels being used
        std::vector<int>    channels_; 
        // Needed to save pin states to let outside program manage interrupts when driving motors
        // As this lets us step between power levels using duty cycle 0-100
        std::vector<int>    pinStates_vec; 


        ////////////////////// End Variables ////////////////////////


        void set_motors(const std::vector<int>& speeds);

        // calculates direction (-1, 0, 1) to step pins toward targets
        std::vector<int> targetDistance(const std::vector<int>& targets);

        // sets the speed of a single motor channel
        void set_motor_speed(int motor_index, float speed);

        // convert percent drive (0-100) to duty cycle for PCA9685
        int percent_drive_to_duty(float percent_drive);

    public:

        //         Parameters
        //         ----------
        //         local_channels : List[int]
        //             List of channels to be using from i2c splitter
        //         num_motors : int
        //             Number of motors equal to len of 'local_channels'
        //         step_size : int, optional
        //             amount to move motors by out of 100, by default 5
        //         """
        MotorCommand(const std::vector<int>& channels, int numMotors, int step_size );

        // implements a incremental movement rather than immediately going to a target speed
        void pinStep(const std::vector<int>& targets);

        std::string pinStates = "STUB: MotorCommand not implemented";

        bool set_pwm(int channel, int on_value);

        void update_pinStates_string();
        
        std::vector<int> get_pinStates_vec() const{
            return pinStates_vec;
        }
};

#endif // MOTOR_COMMAND_HPP
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
 