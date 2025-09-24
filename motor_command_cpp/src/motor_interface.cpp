#ifndef MOTOR_INTERFACE_HPP
#define MOTOR_INTERFACE_HPP


#include "rclcpp/rclcpp.hpp" //ros2 client library
#include <thread> //threading library

// define the class for the motor interface
class MotorInterface()
{
    // This class handles direct control of motors 
    // should be given as an array of ints

    private:
        //define all the variables
        std::vector<int>                   channels;
        float                              major_time;
        int                                max_val;
        float                              minor_time;
        std::unique_ptr<MotorCommand>      motor_commander;
        int                                num_motors;
        int                                offset;
        int                                step_size;
        int                                steps_used;


    public:
        MotorInterface( std::shared_ptr<rclcpp::Node> node, std::vector<int> channel, int numMotors, int offset, int max_val, float minor_time, float major_time, int step_size, int steps_used = 10 )
        {
            //info Number of motors 
            this->num_motors = num_motors

            // info This is the amount of time between steps
            this->minor_time = minor_time

            // info this is the amount of time between new targets being used
            this->major_time = major_time

            // info this is how to set the min val
            this->offset = offset

            // info This is needed as this interface will take percent and scale to output used
            this->max_val = max_val

            //info max steps to go from one extreme to the other
            this->max_steps_needed = (int)(this->max_val / step_size)

            //info this is the amount of steps used assuming motors don't need to reach value
            this->steps_used = steps_used

            // info this is the instance of motorcommand that will be used
            this->motor_commander = std::make_unique<MotorCommand>(channels, this->num_motors, step_size)


        }


        //     def __init__(self, channels: List[int], numMotors: int, offset: int, max_val: int, minor_time: float, major_time: float, step_size: int, steps_used=10) -> None:
//         # info This is the instance of motorcommand that will be used
//         self.motor_commander = MotorCommand(
//             channels, self.numMotors, step_size)
//         # info This is the latest command recieved from ros if ros fails to deliver a new value before next execution then the same values are used
//         self.last_directions: List[int] = []

//         # info New motor targets
//         self.new_directions: bool = False
//         # info Event to signal kill
//         self.stop_event = threading.Event()

}


// # Decleration of wrapper for threading a function
// def threaded(fn):
//     def wrapper(*args, **kwargs):
//         thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
//         thread.start()
//         return thread
//     return wrapper



// class MotorInterface():
//     """Handles direct control of motors
    
//         Should be given an array of ints 
//     """

//     def __init__(self, channels: List[int], numMotors: int, offset: int, max_val: int, minor_time: float, major_time: float, step_size: int, steps_used=10) -> None:
//         # info Number of motors
//         self.numMotors: int = numMotors
//         # info This is the amount of time between steps
//         self.minor_time: float = minor_time
//         # info This is the amount of time between new targets being used
//         self.major_time: float = major_time
//         # info This is the amount of time between new targets being used
//         self.major_time: float = major_time
//         # info This is how to set the min value
//         self.offset: int = offset
//         # info This is needed as this interface will take percent and scale to output used
//         self.max_val: int = max_val
//         # info max steps to go from one extreme to the other
//         self.max_steps_needed: int = int(self.max_val / step_size)
//         # info This is the amount of steps used assuming motors don't need to reach value
//         self.steps_used: int = steps_used
//         # info This is the instance of motorcommand that will be used
//         self.motor_commander = MotorCommand(
//             channels, self.numMotors, step_size)
//         # info This is the latest command recieved from ros if ros fails to deliver a new value before next execution then the same values are used
//         self.last_directions: List[int] = []

//         # info New motor targets
//         self.new_directions: bool = False
//         # info Event to signal kill
//         self.stop_event = threading.Event()


//     def second_setup(self):
//         self.range: int = abs(self.max_val - self.offset)
//         # self.arm_seq()

//     @threaded
//     def arm_seq(self) -> threading.Thread:
//         """Current method of arming all motors may change with calibration

//         Notes
//         -----
//             This is the correct way to set up the motors to run
//         """

//         target_speeds: List[List[int]] = [
//             [0 for _ in range(self.numMotors)],
//             [20 for _ in range(self.numMotors)],
//             [30 for _ in range(self.numMotors)],
//             [10 for _ in range(self.numMotors)]
//         ]

//         for targets in target_speeds:
//             for _ in range(self.max_steps_needed):
//                 self.motor_commander.pinStep(targets)
//                 time.sleep(self.minor_time)

//         self.calling_function()

//     def clo_seq(self) -> None:
//         """Cleans up motors and is responsible for bringing them all back to zero"""

//         targets: List[int] = [0 for _ in range(self.numMotors)]
//         for _ in range(self.max_steps_needed):
//             self.motor_commander.pinStep(targets)
//             time.sleep(self.minor_time)


//     def __percent_to_duty(self, percent: int) -> int:
//         """converts percent to duty in ms pulses

//         Percent is used for it's convience in the rest of the code

//         Parameters
//         ----------
//         percent : int
//             percent 0-100 for running the motors

//         Returns
//         -------
//         int
//             duty in ms pulses
//         """
//         range: int = abs(self.max_val - self.offset)
//         duty: int = int(((percent / 100) * range) + self.offset)
//         return duty

//     def calling_function(self) -> None:
//         """Used to step motors to each target given
        
//         Notes
//         -----
//             Only needs to be called once
//         """
//         while not self.stop_event.is_set():
//             while (self.new_directions):
//                 duty_directions: List[int] = self.direction_to_motor(self.last_directions)
//                 for _ in range(self.steps_used):
//                     self.motor_commander.pinStep(duty_directions)
//                     time.sleep(self.minor_time)
//                 self.new_directions = False
//                 time.sleep(self.major_time)
//             # if taking to many resources change this to major time but minor time is used as to be more responsive
//             time.sleep(self.minor_time)
//         print("Thread exiting")

//     def direction_to_motor(self, directions) -> List[int]:
//         """This function will have some of the direction to motor commands

//         Notes
//         -----
//             directions will be in the form of a list of floats
//                 ['x': -1-1, 'y':-1-1, 'z':-1-1, 'pitch':-1-1, 'yaw':-1-1, 'roll':-1-1]

//             This function is not implemented yet and only contains the translation from percent drive of commands to duty cycle
//         """
//         # * if you wish to go to the negative end of this axis the magnitude must also be supplied as a negative
//         # info For multiple instructions to be followed at once the results post array must be added together while being grouped
//         # info This assumes that all motors are number 1-4 5-8 left to right and horizontal then vertical
//         # ~ This could be used to balance out an under preforming motor
//         motor_to_directions = [
//             [1, 1, -1, -1, 0, 0, 0, 0], # 'x-axis'
//             [1, -1, 1, -1, 0, 0, 0, 0], # 'y-axis'
//             [0, 0, 0, 0, 1, 1, 1, 1], # 'z-axis' 
//             [0, 0, 0, 0, 1, 1, -1, -1], # 'pitch' 
//             [1, -1, -1, 1, 0, 0, 0, 0], # 'yaw' 
//             [0, 0, 0, 0, 1, -1, 1, -1], # 'roll'
//             # Add depth control
//         ]

//         drive_in_duty = [0 for _ in range(self.numMotors)]

//         # ! Not working need to diagnose later <values being passed are not of type directions but are instead just motor controlls>
//         # for index in range(len(directions)):
//         #     for second_index in  range(len(motor_to_directions[0])):
//         #         drive_in_duty[second_index] += directions[index] * motor_to_directions[index][second_index]
//         # ~ Temp fix for above
//         drive_in_duty = directions

//         drive_to_duty = [self.__percent_to_duty(duty) for duty in drive_in_duty]

//         # for p_direction in directions:
//         #     drive_in_duty.append(self.__percent_to_duty(p_direction))
//         return (drive_to_duty)
    

//     def callback(self, message_rec):
//         """Function to subscribe to driver with ros
        
//         This is set up in a way to allow ros and the motor controls to function on a async basis. This will make sure nothing locks up
//         and that pid gets very low latency feedback (not really but kinda).
//         """

//         print("Data received is: " + str(message_rec.data))
//         self.last_directions = message_rec.data
//         # self.calling_function(self.last_directions)
//         self.new_directions = True
//         # This is still set up in a way that is blocking need to incorporate a major time step to do this
//         """ Break down of cases
//         1) Motors finish getting to targets before next instruction is published 
//             They should not start running the steping program until new instructions are given
//         2) Motors finish as new targets arive 
//             Motors should run with this new information as soon as possible
//         3) Motors are not finished steping to targets
//             Motors should finish steping to targets and then start the stepping to the newest target 
//         """
//         # self.calling_function(self.last_directions)