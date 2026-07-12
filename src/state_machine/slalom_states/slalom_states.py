import time
import yasmin
import math
from yasmin import State, Blackboard
from messages.msg import PIDInput, VisionMessage

class SlalomState(State):
    def __init__(self):
        super().__init__(outcomes=["next", "done"])

    def execute(self, blackboard: Blackboard):

        # TODO - align to gate using henry cv

        init_depth = blackboard.get("depth")

        while True:

            msg = PIDInput()

            odom = blackboard.get("odom")

            msg.x_mode = True
            msg.y_mode = True
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = True
            msg.pitch_setpoint = 0.0
            msg.measurement_pitch = odom["pitch"]
            msg.roll_setpoint = 0.0
            msg.measurement_roll = odom["roll"]

            msg.z_setpoint = init_depth + 2
            msg.z_measurement = blackboard.get("depth")

            self.context.pid_publisher.publish(msg)
            
            if(math.abs(msg.z_setpoint - msg.z_measurement) < 0.2):
                break

            time.sleep(0.05)

        msg = PIDInput()

        odom = blackboard.get("odom")

        msg.x_mode = False
        msg.y_mode = True
        msg.z_mode = True
        msg.roll_mode = True
        msg.pitch_mode = True
        msg.yaw_mode = True
        msg.pitch_setpoint = 0.0
        msg.measurement_pitch = odom["pitch"]
        msg.roll_setpoint = 0.0
        msg.measurement_roll = odom["roll"]

        msg.x_power = .5

        self.context.pid_publisher.publish(msg)
            
        while True:
                
            # TODO break after something andrew was saying something about how you can find distance
                break

            time.sleep(0.05)

        return "next"

def get_slalom_state(context):
    state = SlalomState()
    transitions = {
    # TODO - fix this transition and like evreything else frfr
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