# Begin typing imports
from typing import List
# End typing imports

# Begin imports
import busio
from board import SCL, SDA
import adafruit_pca9685 as PCA9685
# End imports

# BEGIN SETUP
i2c = busio.I2C(SCL, SDA)
pca = PCA9685.PCA9685(i2c, address=0x40)
pca.frequency = 48  # Hz, works with BLHeli_32 PWM mode
# END SETUP


class MotorCommand():
    def __init__(self, 
        local_channels: List[int], 
        num_motors: int, 
        step_size: int=5
        ) -> None:
        """_summary_

        A simple Motor object to control the pin states of multiple motors. 
        This commander does not handle timing and instead relies on an external function to handle timing in between both major and minor target changes.

        Parameters
        ----------
        local_channels : List[int]
            List of channels to be using from i2c splitter
        num_motors : int
            Number of motors equal to len of 'local_channels'
        step_size : int, optional
            amount to move motors by out of 100, by default 5
        """

        # info Number of motors being managed
        self.motorNum: int = num_motors

        # info list can only contain -1, 0, 1
        self.motor_direction: List[int] = [1 for _ in range(num_motors)]

        # info How much to move the motors at each minor step
        self.step_size: int = step_size

        # info Needed to save pin states to let outside program manage interupts when driving motors
        # info As this lets us step between power levels using duty cycle 0-100
        self.pinStates: List[int] = [0 for _ in range(num_motors)]

        # info This creates an array of channels to change
        # info This is done so number of motors can be changed on the fly
        self.motors: List[PCA9685.PWMChannel] = [
            pca.channels[channel] for channel in local_channels]

    def __microSec_to_duty(self, microSec: int) -> int:
        """Convert Microsecond pulses to duty cycle for PCA9685

        Convert Microsecond pulses for Bl-Heli32 to duty cycle with current pca frequency of 48. 

        Parameters
        ----------
            microSec : int
                Must be int from 1000-2000µ

        Returns
        -------
            int
                int from 0-65536µ

        Notes
        -----
        'microsec' range comes from ESC's desired control frequency
        The return range comes from the limits of the PCA9685's 16 bit api
        
        """

        """Convert Microsecond pulses to duty cycle for PCA9685"""
        samp_time: float = (1 / pca.frequency) * 1_000_000  # microseconds per cycle
        duty_cycle = int((65536 * microSec) / samp_time)
        return duty_cycle

    def set_motor_speed(self, motor_idex: int, speed: float) -> None:
        '''Set the speed of a single motor (0-100) compatible with BLHeli_32'''

        # Map 0-100% speed to 1000-2000 us pulse for BLHeli_32
        pulse_us = int(1000 + int(speed * 10))  # 0% -> 1000µs, 100% -> 2000µs
        pwm_value = self.__microSec_to_duty(pulse_us)
        self.motors[motor_idex].duty_cycle = pwm_value

    def pinStep(self, targets: List[int]) -> None:
        """Move pin towards target supplied"""

        directions: List[int] = self.__targetDistance(targets)
        for index in range(len(directions)):
            if directions[index] == 0:
                continue

            # Update pinState toward target, avoiding overshoot
            delta = directions[index] * self.step_size
            if abs(delta) >= abs(targets[index] - self.pinStates[index]):
                self.pinStates[index] = targets[index]
            else:
                self.pinStates[index] += delta

        self.__set_motors(self.pinStates)


    def __set_motors(self, speeds: List[int]) -> None:
        """Sets pins to values given by speed position"""

        for index in range(self.motorNum):
            # Clamp speed to 0-100 before sending
            clamped_speed = max(0, min(100, speeds[index]))
            self.set_motor_speed(index, clamped_speed)

    def __targetDistance(self, targets: List[int]) -> List[int]:
        """Figures out wich direction to step pins"""

        values: List[int] = [target - pinState for target, pinState in zip(targets, self.pinStates)]
        conversions: List[int] = [int(value / abs(value)) if value != 0 else 0 for value in values]
        return conversions

