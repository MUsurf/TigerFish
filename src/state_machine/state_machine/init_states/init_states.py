from state_machine.init_states.go_to_depth_state import GoToDepthState

def get_go_to_depth_state(context):
    return "GO_TO_DEPTH_STATE", GoToDepthState(context), {"next_state", "START_GATE_STATE"}

STATE_GETTERS : list = [get_go_to_depth_state]