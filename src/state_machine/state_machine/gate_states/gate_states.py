from state_machine.state_machine.gate_states.align_gate_state import AlignGate
from state_machine.state_machine.gate_states.thru_gate_state import ThruGate
from state_machine.state_machine.gate_states.obtain_depth_state import ObtainDepth



def align_gate_state(context):
    return "ALIGN TO GATE STATE", AlignGate(context), {"next_state", "GO THRU GATE STATE"}
def thru_gate_state(context):
    return "GO THRU GATE STATE", ThruGate(context), {"next_state", "????"}
def obtain_depth_state(context):
    return "OBTAIN DEPTH STATE", ObtainDepth(context), {"thru_gate", "GO THRU GATE STATE"}

STATE_GETTERS : list = [align_gate_state, thru_gate_state]