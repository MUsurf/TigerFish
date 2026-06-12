from state_machine.state_machine.gate_states.align_gate_state import AlignGate
from state_machine.state_machine.gate_states.thru_gate_state import ThruGate
from state_machine.state_machine.gate_states.obtain_depth_state import ObtainDepth
from state_machine.state_machine.gate_states.face_gate_state import FaceGate
from state_machine.state_machine.gate_states.reset_state import ResetState



def face_gate_state(context):
    return "FACE GATE STATE", FaceGate(context), {"next_state" : "ALIGN TO GATE STATE", "obtain_depth" : "OBTAIN DEPTH STATE", "reset" : "RESET STATE"}
def align_gate_state(context):
    return "ALIGN TO GATE STATE", AlignGate(context), {"next_state" : "GO THRU GATE STATE", "obtain_depth" : "OBTAIN DEPTH STATE", "reset" : "RESET STATE"}
def thru_gate_state(context):
    return "GO THRU GATE STATE", ThruGate(context), {"next_state" : "????", "obtain_depth" : "OBTAIN DEPTH STATE", "reset" : "RESET STATE"}
def obtain_depth_state(context):
    return "OBTAIN DEPTH STATE", ObtainDepth(context), {"face_gate" : "FACE GATE STATE", "thru_gate" : "GO THRU GATE STATE", "align_gate" : "ALIGN TO GATE STATE", "reset" : "RESET STATE"}
def reset_state(context):
    return "RESET STATE", ResetState(context), {"face_gate" : "FACE GATE STATE", "thru_gate" : "GO THRU GATE STATE", "align_gate" : "ALIGN TO GATE STATE", "reset" : "RESET STATE"}


STATE_GETTERS : list = [face_gate_state, align_gate_state, thru_gate_state, reset_state, obtain_depth_state]