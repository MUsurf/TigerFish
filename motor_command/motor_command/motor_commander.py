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
pca.frequency = 400  # Hz, works with BLHeli_32 PWM mode
# END SETUP


class MotorCommand():
    def __init__(self, 
        local_channels: List[int], 
        num_motors: int, 
        step_size: int = 2.5
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
        

    def _percent_drive_to_duty(self, percent_drive: float) -> int:
        """Convert percent drive to duty cycle for PCA9685

        Convert percent drive for Bl-Heli32 to duty cycle with current pca frequency of 48.

        Parameters
        ----------
            percent_drive : int
                Must be -100%-100%

        Returns
        -------
            int
                int from 0-65536µ

        Notes
        -----
        We convert percent drive to map biderectional percents to a 1000μ - 2000μ with 1500μ being the center value.

        'microsec' range comes from ESC's desired control frequency
        The return range comes from the limits of the PCA9685's 16 bit api
        
        """
        """Convert percent drive to microsecond"""
        # Map 0-100% speed to 1000-2000 us pulse for BLHeli_32
        micro_sec = int(1000 + int((percent_drive + 100) * 5))

        """Convert Microsecond pulses to duty cycle for PCA9685"""
        samp_time: float = (1 / pca.frequency) * 1_000_000  # microseconds per cycle
        duty_cycle = int((65536 * micro_sec) / samp_time)
        return duty_cycle
    
    # def _percent_drive_to_duty(self, percent_drive: float) -> int:
    #     min_us, max_us = 1000, 2000  # safe defaults, but make configurable
    #     if(percent_drive <= 0) : min_us = 1000
    #     micro_sec = int(min_us + (percent_drive / 100) * (max_us - min_us))
    #     samp_time = (1 / pca.frequency) * 1_000_000
    #     return int((65536 * micro_sec) / samp_time)

    def set_motor_speed(self, motor_idex: int, speed: float) -> float:
        '''Set the speed of a single motor (0-100) compatible with BLHeli_32'''

        pwm_value = self._percent_drive_to_duty(speed)
        self.motors[motor_idex].duty_cycle = pwm_value
        return pwm_value
        

    def pinStep(self, targets: List[int]):
        """Move pin towards target supplied"""

        directions: List[int] = self._targetDistance(targets)
        for index in range(len(directions)):
            if directions[index] == 0:
                continue

            # Update pinState toward target, avoiding overshoot
            delta = directions[index] * self.step_size
            if abs(delta) >= abs(targets[index] - self.pinStates[index]):
                self.pinStates[index] = targets[index]
            else:
                self.pinStates[index] += delta

        return self._set_motors(self.pinStates)


    def _set_motors(self, speeds: List[int]) -> List[int]:
        """Sets pins to values given by speed position"""
        pwm_values = []
        for index in range(self.motorNum):
            # Clamp speed to 0-100 before sending
            clamped_speed = max(0, min(100, speeds[index]))
            pwm_values.append(self.set_motor_speed(index, clamped_speed))
        return pwm_values

    def _targetDistance(self, targets: List[int]) -> List[int]:
        """Figures out which direction to step pins"""

        values: List[int] = [target - pinState for target, pinState in zip(targets, self.pinStates)]
        conversions: List[int] = [int(value / abs(value)) if value != 0 else 0 for value in values]
        return conversions

