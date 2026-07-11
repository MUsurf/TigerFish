import time
import yasmin
from yasmin import State, Blackboard
from messages.msg import PIDInput, VisionMessage

class SlalomState(State):
    def __init__(self):
        super().__init__(outcomes=["next", "done"])

        self.frequency = 10.0 # Hz

    def execute(self, blackboard: Blackboard):

        Gates_Gone_Through = 0

        # TODO: this has to be a safe while loop, so make sure there is a timer on how long it can run, and do some thread.sleep so you are not taking all execution time

        # TODO: make sure this handles depth (aka the pid or whatever)

        while Gates_Gone_Through != 3:

            # all steps should prob be their own while loop

            # Find the red

            # center yourself with it (aka put it in the middle of the camera by spinning) and optionally all of them (this would take more movement)

            while percent_of_vision < 50:
                msg = PIDInput()
                msg.z_mode = True
                msg.roll_mode = True
                msg.pitch_mode = True
                msg.yaw_mode = False
                msg.yaw_power = yaw_power
                msg.z_measurement = depth 
                msg.z_setpoint = self.desired_depth
                msg.pitch_setpoint = 0.0
                msg.measurement_pitch = odom["pitch"]
                msg.roll_setpoint = 0.0
                msg.measurement_roll = odom["roll"]
                self.context.pid_publisher.publish(msg)

                time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))

            # inch forward until it takes up a percentage of vision

            # back up slightly, move left/right, move forward a set distance

            Gates_Gone_Through += 1

            # TODO - obviously remove this, but you also should have a timer condition on how long the task should be aloower to run before just killing it and calling it a day
            if True:
                break





        # use blackboard["odom"], blackboard["depth"], etc.
        return "next"

def get_slalom_state(context):
    state = SlalomState()
    transitions = {
        "next": "NEXT_STATE_NAME",
        "done": "complete",
    }
    return "SLALOM", state, transitions

STATE_GETTERS = [
    get_slalom_state,
]

# dont totatly trust above, was ai generated

# IMPORTANT NOTE: if we are only doing like 2-3 tasks, we should definitely hard code the order, and dont let this state take over when red, cause gate could trigger it

# General Idea:
#
# This step might be a more last minute thing, but if you line up every red pole within certain field of view,
# you can guarentee that you are coming at it somewhat head on (check image, there are also only 3, maybe could do something with this?)
#
# First step, go directly at the red until it enters some amount of your vision
#
# Second step, go slightly back, right/left (depending on which you went through at the start), then forward for a little
#
# Then just repeat the steps
#
# Im sure you could also add some other checks that could make it more reliable, but this seems to be a pretty good general idea