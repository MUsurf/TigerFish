from state_machine.state_machine.start_states.start_state import StartState
from state_machine.state_machine.start_states.end_state import EndState


def get_start_state(context):
    return "START_STATE", StartState(context), {"started" : "OBTAIN_DEPTH_STATE"}

def get_end_state(context):
    return "END_STATE", EndState(context), {}

STATE_GETTERS : list = [get_start_state, get_end_state]
