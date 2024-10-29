
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
pca.frequency = 280  # Hz
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
        """Convert Microsecond pulses to duty cycle

        Convert Microsecond length pulses that have been aligned with the operating requirments of the interface to duty cycle of the current PWM frequency

        Parameters
        ----------
            microSec : int
                Must be int from 0-100 'microSec'

        Returns
        -------
            int
                int from 65536-0

        Notes
        -----
        'microsec' range comes from pca chips desired control frequency
        
        """

        samp_time: float = (1/pca.frequency) * 1000 * \
            1000  # Convert to Micro Sec
        duty_cycle = int((65536 * microSec)/(samp_time))
        return duty_cycle

    def set_motor_speed(self, motor_idex: int, speed: int) -> None:
        '''Set the speed of a single motor'''

        pwm_value: int = self.__microSec_to_duty(1000 + (speed * 10))
        self.motors[motor_idex].duty_cycle = pwm_value

    def pinStep(self, targets: List[int]) -> None:
        """Move pin towards target supplied

        Generates intermediate values and then steps pin from current state toward target.

        Parameters
        ----------
            targets : List[int]
                list of targets for motors (order matters).

        Notes
        -----
            Should be used with an outside function to handle interupts and timing changes
        """

        directions: List[int] = self.__targetDistance(targets)
        for index in range(len(directions)):
            if (directions[index] == 0):
                continue
            self.pinStates[index] += directions[index] * self.step_size
            # print(self.pinStates[index])
        self.__set_motors(self.pinStates)

    def __targetDistance(self, targets: List[int]) -> List[int]:
        """Figures out wich direction to step pins

        Notes
        -----
            Reworked

        """

        values: List[int] = [target - pinState for target, pinState in zip(targets, self.pinStates)]
        conversions: List[int] = [int(value / abs(value)) if value != 0 else 0 for value in values] # int cast should only be necessary for linter
        return (conversions)

    def __set_motors(self, speeds: List[int]) -> None:
        """Sets pins to values given by speed position"""

        for index in range(self.motorNum):
            self.set_motor_speed(index, speeds[index])


# Begin typing imports
from typing import List
# End typing imports

# Begin imports
from motor_commander import MotorCommand
import time
# End imports

class MotorInterface():
    """Handles direct control of motors
    
        Should be given an array of ints 
    """

    def __init__(self, channels: List[int], numMotors: int, offset: int, max_val: int, minor_time: float, major_time: float, step_size: int, steps_used=10) -> None:
        # info Number of motors
        self.numMotors: int = numMotors
        # info This is the amount of time between steps
        self.minor_time: float = minor_time
        # info This is the amount of time between new targets being used
        self.major_time: float = major_time
        # info This is how to set the min value
        self.offset: int = offset
        # info This is needed as this interface will take percent and scale to output used
        self.max_val: int = max_val
        # info max steps to go from one extreme to the other
        self.max_steps_needed: int = int(self.max_val / step_size)
        # info This is the amount of steps used assuming motors don't need to reach value
        self.steps_used: int = steps_used
        # info This is the instance of motorcommand that will be used
        self.motor_commander = MotorCommand(
            channels, self.numMotors, step_size)
        # info This is the latest command recieved from ros if ros fails to deliver a new value before next execution then the same values are used
        self.last_directions: List[int] = []

    def second_setup(self):
        self.range: int = abs(self.max_val - self.offset)
        self.new_directions : bool = False
        self.arm_seq()

    def arm_seq(self) -> None:
        """Current method of arming all motors may change with calibration

        Notes
        -----
            This is the correct way to set up the motors to run
        """

        target_speeds: List[List[int]] = [
            [0 for _ in range(self.numMotors)],
            [20 for _ in range(self.numMotors)],
            [30 for _ in range(self.numMotors)],
            [10 for _ in range(self.numMotors)]
        ]

        for targets in target_speeds:
            for _ in range(self.max_steps_needed):
                self.motor_commander.pinStep(targets)
                time.sleep(self.minor_time)

        self.calling_function()

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""

        targets: List[int] = [0 for _ in range(self.numMotors)]
        for _ in range(self.max_steps_needed + 1):
            self.motor_commander.pinStep(targets)
            time.sleep(self.minor_time)

    def __percent_to_duty(self, percent: int) -> int:
        """converts percent to duty in ms pulses

        Percent is used for it's convience in the rest of the code

        Parameters
        ----------
        percent : int
            percent 0-100 for running the motors

        Returns
        -------
        int
            duty in ms pulses
        """
        range: int = abs(self.max_val - self.offset)
        duty: int = int(((percent / 100) * range) + self.offset)
        return duty

    def calling_function(self) -> None:
        """Used to step motors to each target given
        
        Notes
        -----
            Only needs to be called once
        """
        while (True):
            while (self.new_directions):
                duty_directions: List[int] = self.direction_to_motor(self.last_directions)
                for _ in range(self.steps_used):
                    self.motor_commander.pinStep(duty_directions)
                    time.sleep(self.minor_time)
                time.sleep(self.major_time)
            # if taking to many resources change this to major time but minor time is used as to be more responsive
            time.sleep(self.minor_time)

    def direction_to_motor(self, directions) -> List[int]:
        """This function will have some of the direction to motor commands

        Notes
        -----
            directions will be in the form of a list of floats
                ['x': -1-1, 'y':-1-1, 'z':-1-1, 'pitch':-1-1, 'yaw':-1-1, 'roll':-1-1]

            This function is not implemented yet and only contains the translation from percent drive of commands to duty cycle
        """
        # * if you wish to go to the negative end of this axis the magnitude must also be supplied as a negative
        # info For multiple instructions to be followed at once the results post array must be added together while being grouped
        # info This assumes that all motors are number 1-4 5-8 left to right and horizontal then vertical
        # ~ This could be used to balance out an under preforming motor
        motor_to_directions = [
            [1, 1, -1, -1, 0, 0, 0, 0], # 'x-axis'
            [1, -1, 1, -1, 0, 0, 0, 0], # 'y-axis'
            [0, 0, 0, 0, 1, 1, 1, 1], # 'z-axis' 
            [0, 0, 0, 0, 1, 1, -1, -1], # 'pitch' 
            [1, -1, -1, 1, 0, 0, 0, 0], # 'yaw' 
            [0, 0, 0, 0, 1, -1, 1, -1], # 'roll'
            # Add depth control
        ]

        drive_in_duty = [0 for _ in range(self.numMotors)]

        # ! Not working need to diagnose later <values being passed are not of type directions but are instead just motor controlls>
        # for index in range(len(directions)):
        #     for second_index in  range(len(motor_to_directions[0])):
        #         drive_in_duty[second_index] += directions[index] * motor_to_directions[index][second_index]
        # ~ Temp fix for above
        drive_in_duty = directions

        drive_to_duty = [self.__percent_to_duty(duty) for duty in drive_in_duty]

        # for p_direction in directions:
        #     drive_in_duty.append(self.__percent_to_duty(p_direction))
        return (drive_to_duty)
    

    def callback(self, message_rec):
        """Function to subscribe to driver with ros
        
        This is set up in a way to allow ros and the motor controls to function on a async basis. This will make sure nothing locks up
        and that pid gets very low latency feedback (not really but kinda).
        """

        print("Data received is: " + str(message_rec.data))
        self.last_directions = message_rec.data
        self.new_directions = True
        # This is still set up in a way that is blocking need to incorporate a major time step to do this
        """ Break down of cases
        1) Motors finish getting to targets before next instruction is published 
            They should not start running the steping program until new instructions are given
        2) Motors finish as new targets arive 
            Motors should run with this new information as soon as possible
        3) Motors are not finished steping to targets
            Motors should finish steping to targets and then start the stepping to the newest target 
        """
        # self.calling_function(self.last_directions)