# import rclpy
# from rclpy.node import Node
from state_machine_interface import State, Transition, StateMachine
import time

class GateState(State):
    def on_entry(self, event_data=None):
        # what should we do on entry??
        print("Entering Gate State")

    def on_exit(self, event_data=None):
        # what should we do on exit??
        print("Exiting Gate State")

    def execute(self, event_data=None):
        print("Gate state executing...")
        # static have_captured_image
        # 
        # begin rotation
        # 
        # while not see_gate:
        #    rotate
        #    if see_gate:
        #        stop rotation
        #        break
        #
        # while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #   move to align gate
        #   if gate_aligned:
        #       stop moving
        #       break
        # if not have_captured_image:
        #
        #   chose_gate = choose_gate()
        #
        #   capture_image()
        #
        #   process_and_store_image()
        #
        # have_captured_image = true
        #
        # while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #   move towards chose_gate
        #   if through_gate:
        #       stop moving
        #       break
        #
        # done

class SlalomState(State):
    def on_entry(self, event_data=None):
        # what should we do on entry?? prob align with first
        print("Entering Slalom State")

    def on_exit(self, event_data=None):
        # what should we do on exit??
        print("Exiting Slalom State")

    def execute(self, event_data=None):
        print("Slalom state executing...")
        # while see_slalom:
        #   while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #       move to align slalom
        #       if slalom_aligned:
        #           stop moving
        #           break
        #
        #   Note: maybe alignment should be handled during movement? maybe not? idk
        #
        #   while true: (note: maybe this should be a time constraint? E.G. while not 5 minutes have past)
        #       move towards chose_gate
        #       if through_gate:
        #           stop moving
        #           break
        #
        # done


class TorpedoState(State):
    def on_entry(self, event_data=None):
        print("Entering Torpedo State")

    def on_exit(self, event_data=None):
        print("Exiting Torpedo State")

    def execute(self, event_data=None):
        print("Torpedo state executing...")

class StateMachineNode():
    def __init__(self):
        # super().__init__('state_machine_node')
        # Create states
        gate_state = GateState()
        slalom_state = SlalomState()
        torpedo_state = TorpedoState()
        
        # Create state machine
        self.sm = StateMachine(gate_state)
        # Add a simple transition that always fires (for demonstration)
        self.sm.add_transition(gate_state, Transition(slalom_state, lambda event: True))
        self.sm.add_transition(slalom_state, Transition(torpedo_state, lambda event: True))
        self.sm.add_transition(torpedo_state, Transition(gate_state, lambda event: True))
        
        # Set up a timer to trigger state machine execution periodically.
        # self.timer = self.create_timer(2.0, self.timer_callback)

    def timer_callback(self):
        # Process an event and run the current state.
        if self.sm.process_event():
            print("Transitioning to new state.")

            # System logic to decide if a transition should occur
            # For this example, we always transition to the next state.

            self.sm.start_event()  # Start the new state
            self.sm.run() # Run the new state
        else:
            print("No transition occurred.")
            # If no transition occurred, keep iterating on current task.
            self.sm.run() # Run the current state

def main(args=None):
    rclpy.init(args=args)
    node = StateMachineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

def local_main():
    # This is a local main function to run the state machine without ROS.
    node = StateMachineNode()
    node.timer_callback()  # Call the timer callback to start the state machine
    while(True):
        node.timer_callback()  # Simulate the timer callback
        time.sleep(2)

if __name__ == '__main__':
    local_main()