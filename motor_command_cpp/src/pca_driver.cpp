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

#include "motor_command_cpp/pca_driver.hpp"

// Includes ////////////////////
#include <fcntl.h>      // open
#include <unistd.h>     // close, read, write
#include <sys/ioctl.h>  // ioctl
#include <linux/i2c-dev.h> 
#include <iostream>
#include <cmath>
#include <cstdint>

// Register definitions ////////
#define MODE1       0x00
#define PCA9685_address 0x40
#define PRESCALE    0xFE
#define MODE1_RESTART 0x80
#define MODE1_SLEEP   0x10
#define LED0_ON_L   0x06

////////////////////////////////

//// Constructor /////////////////
PWMDriver::PWMDriver(const std::string& device_path, int address) {
    // Open the I2C bus
    this->i2c_fd = open(device_path.c_str(), O_RDWR);
    if (this->i2c_fd < 0) {
        std::cerr << "Failed to open I2C bus: " << device_path << std::endl;
        return;
    }   

    // Set the I2C address for the PCA9685
    if (ioctl(this->i2c_fd, I2C_SLAVE, address) < 0) {
        std::cerr << "PwmDriver Error: Failed to set I2C address: " << std::hex << address << std::dec << std::endl;
        close(this->i2c_fd);
        this->i2c_fd = -1;
        return;
    }

    // Initialize PCA9685
    writeRegister(MODE1, 0x00); // Normal mode
}
////////////////////////////////

//// Destructor /////////////////
PWMDriver::~PWMDriver() {
    if (this->i2c_fd >= 0) {
        close(this->i2c_fd);
    }
}
////////////////////////////////

//// Write Register /////////////
bool PWMDriver::writeRegister(int reg, unsigned char value) {
    if (this->i2c_fd < 0) { return false; }
    unsigned char buffer[2] = { (unsigned char)reg, value };
    if (write(this->i2c_fd, buffer, 2) != 2) {
        std::cerr << "PwmDriver Error: Failed to write to register " << std::hex << reg << std::dec << std::endl;
        return false;
    }
    return true;
}
////////////////////////////////

uint8_t PWMDriver::readRegister(int reg) {
    //check if file descriptor is valid
    if(this->i2c_fd < 0) { return 0; }

    // write the register address to read from
    unsigned char buffer_write[1] = { (unsigned char)reg};
    if (write(this->i2c_fd, buffer_write, 1) != 1) {
        std::cerr << "PwmDriver Error: Failed to write to register " << std::hex << reg << std::dec << std::endl;
        return 0;
    }   

    // read the value from the register
    unsigned char buffer_read[1];
    if (read(this->i2c_fd, buffer_read, 1) != 1) {
        std::cerr << "PwmDriver Error: Failed to read from register " << std::hex << reg << std::dec << std::endl;
        return 0;
    }

    return buffer_read[0];
}


//// Set PWM Frequency ///////////
bool PWMDriver::setPWMFreq(int freq) {
    if (this->i2c_fd < 0) { return false; }

    // calculate prescale value based on desired frequency
    // formula: prescaleVal = round(osc_clock / (4096 * freq)) - 1
    // where osc_clock is typically 25MHz for PCA9685
    float prescaleval = 25000000.0; // 25MHz
    prescaleval /= 4096.0;           // 12-bit
    prescaleval /= freq;
    prescaleval -= 1.0;

    unsigned char prescale = (uint8_t) std::round(prescaleval);

    // read the current MODE1 register
    uint8_t oldmode = readRegister(MODE1);

    // put the chip to sleep to set prescale
    uint8_t newmode = (oldmode & 0x7F) | MODE1_SLEEP; //0x7f clears the restart bit
    if (!writeRegister(MODE1, newmode)) {
        return false;
    }

    // set prescale
    if (!writeRegister(PRESCALE, prescale)) {
        return false;
    }

    // wake the chip up (MODE1, restart bit (0x80) | oldmode)
    if (!writeRegister(MODE1, oldmode)) {
        return false;
    }

    // wait for oscillator to stabilize (minimal sleep)
    usleep(500);

    // restart the chip's PWM
    if (!writeRegister(MODE1, oldmode | MODE1_RESTART)) {
        return false;
    }

    return true;
}
////////////////////////////////


// define writing to a single PWM channel /////////////

bool PWMDriver::set_pwm(int channel, int on_value) {
    if (this->i2c_fd < 0) { return false; }
    if (channel < 0 || channel > 15) {
        std::cerr << "PwmDriver Error: Channel must be between 0 and 15." << std::endl;
        return false;
    }
    if (on_value < 0 || on_value > 4095) {
        std::cerr << "PwmDriver Error: on_value must be between 0 and 4095." << std::endl;
        return false;
    }

    int reg_base = LED0_ON_L + 4 * channel;
    if(!writeRegister(reg_base, on_value & 0xFF)) {return false; }            // LEDn_ON_L
    if(!writeRegister(reg_base + 1, (on_value >> 8) & 0xFF)) {return false; } // LEDn_ON_H
    if(!writeRegister(reg_base + 2, 0)) {return false; }                      // LEDn_OFF_L
    if(!writeRegister(reg_base + 3, 0)) {return false; }                     // LEDn_OFF_H

    return true;
}