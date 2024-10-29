
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
    def __init__(self, local_channels: List[int], num_motors: int, step_size=5, minor_time=.1) -> None:
        # info Number of motors being managed
        self.motorNum: int = num_motors

        # info list can only contain -1, 0, 1
        self.motor_direction: List[int] = [1 for _ in range(num_motors)]

        # info How much to move the motors at each minor step
        self.step_size: int = step_size

        # info Set how much time to wait on arming
        self.minor_step: float = minor_time

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
            Should be used with an outside function to handle interupts
        """

        directions: List[int] = self.__targetDistance(targets)
        for index in range(len(directions)):
            if (directions[index] == 0):
                continue
            self.pinStates[index] += directions[index] * self.step_size
            print(self.pinStates[index])
        # ? Sets every pin even if it is already opperating at that speed
        # ? Don't think this is an area that needs to be improved but is an easy target
        self.__set_motors(self.pinStates)

    def __targetDistance(self, targets: List[int]) -> List[int]:
        """Figures out wich direction to step pins

        Notes
        -----
            Reworked

        """

        values: List[int] = [target - pinState for target, pinState in zip(targets, self.pinStates)]
        conversions: List[int] = [int(value / abs(value)) if value != 0 else 0 for value in values] # int cast should only be nessisary for linter
        return (conversions)

    def __set_motors(self, speeds: List[int]) -> None:
        """Sets pins to values given by speed position"""

        for index in range(self.motorNum):
            self.set_motor_speed(index, speeds[index])

# Begin typing imports
from typing import List
# End typing imports

# Begin imports
import time
# End imports

class MotorInterface():
    """Handles direct control of motors
    
        Should be given an array of ints 
    """

    def __init__(self, channels: List[int], numMotors: int, offset: int, max_val: int, minor_time: float, step_size: int, steps_used=10) -> None:
        # info Number of motors
        self.numMotors: int = numMotors
        # info This is the amount of time between steps
        self.minor_time: float = minor_time
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
            channels, self.numMotors, step_size, self.minor_time)
        # info This is the latest command recieved from ros if ros fails to deliver a new value before next execution then the same values are used
        self.last_directions: List[int] = []

    def arm_seq(self) -> None:
        """Current method of arming all motors may change with calibration

        Notes
        -----
            Pin target values are hardcoded they should not need to be changed often.
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

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""

        num_runs: int = self.max_steps_needed + 1
        targets: List[int] = [0 for _ in range(self.numMotors)]
        for _ in range(num_runs):
            self.motor_commander.pinStep(targets)
            time.sleep(self.minor_time)

    def __percent_to_duty(self, percent: int) -> int:
        range: int = abs(self.max_val - self.offset)
        duty: int = int(((percent / 100) * range) + self.offset)
        return duty

    def calling_function(self, directions) -> None:
        """Used to step motors to each target given"""

        duty_directions: List[int] = self.direction_to_motor(directions)
        for _ in range(self.steps_used):
            self.motor_commander.pinStep(duty_directions)
            time.sleep(self.minor_time)

    def direction_to_motor(self, directions) -> List[int]:
        """This function will have some of the direction to motor commands

        Notes
        -----
            directions will be in the form of a list of floats
                ['x': -1-1, 'y':-1-1, 'z':-1-1, 'pitch':-1-1, 'yaw':-1-1, 'roll':-1-1]

            This function is not implemented yet and only contains the translation from percent drive of commands to duty cycle
        """
        # * if you wish to go to the negative end of this axis the mangintude must also be supplied as a negative
        # info For multiple instructions to be followed at once the results post array must be added together
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

        #for index in range(len(directions)):
        #    for second_index in  range(len(motor_to_directions[0])):
        #        drive_in_duty[second_index] += directions[index] * motor_to_directions[index][second_index]
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
        self.calling_function(self.last_directions)


#!/usr/bin/env python3

'''
ROS 
---

node:
-----
    - motor_listener

Publishes:
----------

Subscribes:
----------
    - motor_command

'''


# Begin typing imports
from typing import List
# End typing imports

# remove
# remove 

# Begin imports
import rospy

from std_msgs.msg import Int32MultiArray
# End imports

# Rospy nodes
rospy.init_node("motor_listener")
rate = rospy.Rate(100)


# Motor init codes
try:
    # Set up for 8 motors should be typical set up
    # Next thing to do is mock the motors
    local_channels: List[int] = [x for x in range(8)]
    num_motors: int = len(local_channels)
    motor_caller = MotorInterface(local_channels, num_motors, 0, 100, .1, 5)

    # high: List[int] = [20 for i in range(num_motors)]
    # low: List[int] = [30 for i in range(num_motors)]

    print("arming")
    motor_caller.arm_seq()
    print("done arming")
    while not rospy.is_shutdown():
        rospy.Subscriber("motor_command", Int32MultiArray, motor_caller.callback)
        # rospy.Subscriber("volt_low", Bool, loop.cut_motors)
        rospy.spin()
    motor_caller.clo_seq()

except KeyboardInterrupt:
    motor_caller.clo_seq()
