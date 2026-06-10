from state_machine.state_machine.gate_states.align_gate_state import AlignGate
from state_machine.state_machine.gate_states.thru_gate_state import ThruGate



def align_gate_state(context):
    return "ALIGN TO GATE STATE", AlignGate(context), {"next_state", "GO THRU GATE STATE"}
def thru_gate_state(context):
    return "GO THRU GATE STATE", ThruGate(context), {"next_state", "????"}

STATE_GETTERS : list = [align_gate_state, thru_gate_state]