# Begin typing imports
from typing import List
# End typing imports

# Begin imports
from motor_command.motor_commander import MotorCommand
import time
import threading
# End imports

# Decleration of wrapper for threading a function
def threaded(fn):
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper



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
            channels, 
            self.numMotors, 
            step_size)
        # info This is the latest command recieved from ros if ros fails to deliver a new value before next execution then the same values are used
        self.last_directions: List[int] = []

        # info New motor targets
        self.new_directions: bool = False
        # info Event to signal kill
        self.stop_event = threading.Event()
        
        self.logging_node = None
        


    def second_setup(self):
        self.range: int = abs(self.max_val - self.offset)
        # self.arm_seq()

    @threaded
    def arm_seq(self):
        """Current method of arming all motors may change with calibration

        Notes
        -----
            This is the correct way to set up the motors to run
        """

        target_speeds: List[List[int]] = [
            [0 for _ in range(self.numMotors)],
            #[20 for _ in range(self.numMotors)],
            #[30 for _ in range(self.numMotors)],
            #[10 for _ in range(self.numMotors)]
        ]

        for targets in target_speeds:
            for _ in range(self.max_steps_needed):
                self.motor_commander.pinStep(targets)
                time.sleep(self.minor_time)
        
        print("Motors armed")

        self.calling_function()

    def clo_seq(self) -> None:
        """Cleans up motors and is responsible for bringing them all back to zero"""

        targets: List[int] = [0 for _ in range(self.numMotors)]
        for _ in range(self.max_steps_needed):
            self.motor_commander.pinStep(targets)
            time.sleep(self.minor_time*10)


    def __percent_to_duty(self, percent: int) -> int:
        """WARN This function is deprecated as it's functionality has been moved to motor commander"""
        return 0 

    def calling_function(self) -> None:
        """Continuously updates motors toward the latest directions in real time."""
        while not self.stop_event.is_set():
            if not self.last_directions:
                time.sleep(self.minor_time)
                continue

            duty_directions = self.direction_to_motor(self.last_directions)

            # Single incremental step toward latest target
            self.motor_commander.pinStep(duty_directions)

            if self.logging_node is not None:
                self.logging_node.get_logger().info(f'Pin states: {self.motor_commander.pinStates}')

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

        # drive_to_duty = [self.__percent_to_duty(duty) for duty in drive_in_duty]
        

        # for p_direction in directions:
        #     drive_in_duty.append(self.__percent_to_duty(p_direction))
        return (drive_in_duty)
    

    def callback(self, message_rec):
        """Function to subscribe to driver with ros
        
        This is set up in a way to allow ros and the motor controls to function on a async basis. This will make sure nothing locks up
        and that pid gets very low latency feedback (not really but kinda).
        """

        print("Data received is: " + str(message_rec.data))
        self.last_directions = message_rec.data
        # self.calling_function(self.last_directions)
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