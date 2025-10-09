#include "motor_command_cpp/motor_command.hpp"

#include <iostream>
const float PCA_FREQUENCY = 48.0f;

MotorCommand::MotorCommand(const std::vector<int>& channels, int numMotors, int step_size ) 
: 
    motorNum(numMotors),
    motor_direction(std::vector<int>(numMotors, 1)),
    step_size(step_size),
    pca("/dev/i2c-1", 0x40),
    channels_(channels),
    pinStates_vec(std::vector<int>(numMotors, 0))
{
    if(!this->pca.setPWMFreq(PCA_FREQUENCY)) // Set frequency to 48.0f Hz for ESCs
    {
        std::cerr << "PwmDriver Error: Failed to set PWM frequency." << std::endl;
    }
}
// sets pins to values given by speed position
void MotorCommand::set_motors(const std::vector<int>& speeds)
{
    for (size_t i = 0; i< motorNum; ++i)
    {
        int clamped_speed = std::max(0, std::min(100, speeds[i])); // Clamp speed to [0, 100]
        set_motor_speed(i, clamped_speed);
    }
}

// sets the speed of a single motor channel
void MotorCommand::set_motor_speed(int motor_index, float speed)
{
    int pwm_val = percent_drive_to_duty(speed);
    this->pca.set_pwm(channels_[motor_index], pwm_val);
}

// convert percent drive (0-100) to duty cycle for PCA9685
int MotorCommand::percent_drive_to_duty(float percent_drive)
{
    int micro_sec = int(1000 + int(percent_drive * 10)); // Map 0-100% to 1000-2000us

    //convert microsecond pulses to duty cycle for PCA9685
    float sample_time = (1 / PCA_FREQUENCY) * 1e6; // in microseconds
    int duty_cycle = int((65536 * micro_sec) /sample_time);
    return duty_cycle;
}   


// implements a incrementa movement rather than immediately going to a target speed
void MotorCommand::pinStep(const std::vector<int>& targets)
{
    std::vector<int> step_directions = this->targetDistance(targets);
    for (size_t i = 0; i < step_directions.size() ; ++i)
    {
        if(step_directions[i] != 0) // Only update if there's a change
        {
            int delta = step_directions[i] * this->step_size;

            //check if the step overshoots the target
            if (std::abs(delta) >= std::abs(targets[i] - this->pinStates_vec[i]))
            {
                this->pinStates_vec[i] = targets[i]; // Directly set to target if overshooting
            }
            else
            {
                this->pinStates_vec[i] += delta; // Incrementally step towards target
            }
           
        }
        // clamp speed between 0 and 100
        this->pinStates_vec[i] = std::max(0, std::min(100, this->pinStates_vec[i]));
    }
    //update the motor
    this->set_motors(pinStates_vec);

    this->update_pinStates_string();
}


std::vector<int> MotorCommand::targetDistance(const std::vector<int>& targets) 
{
    std::vector<int> conversions(targets.size());

    for(size_t i = 0; i<targets.size(); ++i)
    {
        int diff = targets[i] - this->pinStates_vec[i];
        if (diff > 0)
        {
            conversions[i] = 1; // Need to increase speed   
        }
        else if (diff < 0)
        {
            conversions[i] = -1; // Need to decrease speed
        }
        else
        {
            conversions[i] = 0; // Already at target
        }
    }

    return conversions;
}

void MotorCommand::update_pinStates_string()
{
    std::ostringstream oss;
    oss << "Motor States: [";
    for (size_t i = 0; i < pinStates_vec.size(); ++i) {
        oss << pinStates_vec[i];
        if (i != pinStates_vec.size() - 1) oss << ", ";
    }
    oss << "]";
    pinStates = oss.str();
}
