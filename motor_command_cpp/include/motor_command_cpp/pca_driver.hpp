

////////////////////////////////////////////////////////////////////////////////////////////////////////////
// So there really isn't a simple library
// like adafruit for C++ to handle PCA9685
// So this is a wrapper around the i2c-dev library
// to handle the low level i2c communication
// with the PCA9685 chip
// This is a very basic implementation and does not
// handle all the features of the PCA9685.
//
// It should be noted that most of this code is likely AI generated code or derived from AI code
///////////////////////////////////////////////////////////////////////////////////////////////////////////
#ifndef PWM_DRIVER_HPP
#define PWM_DRIVER_HPP

#include <string>
#include <cstdint> // for uint8_t


class PWMDriver
{
    private:
        int i2c_fd = -1;

        //helper function to read/write registers
        bool writeRegister(int reg, uint8_t value);
        uint8_t readRegister(int reg);

    public:
        //constructor: 
        // device_path: I2C bus device path, e.g. "/dev/i2c-1"
        // address: I2C address of the PCA9685, default is 0x40
        PWMDriver(const std::string& device_path = "/dev/i2c-1", int address = 0x40);


        // Destructor to close the I2C file descriptor
        ~PWMDriver();

        // public method to set PWM frequency (in Hz)
        bool setPWMFreq(int freq);
        bool set_pwm(int channel, int on_value);

        
};

#endif // PWM_DRIVER_HPP