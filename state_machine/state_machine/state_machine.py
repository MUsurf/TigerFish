import rclpy
from rclpy.node import Node
from state_machine_interface import State, Transition, StateMachine

class IdleState(State):
    def on_entry(self, event_data=None):
        print("Entering Idle State")

    def on_exit(self, event_data=None):
        print("Exiting Idle State")

    def execute(self, event_data=None):
        print("Idle state executing...")

class ActiveState(State):
    def on_entry(self, event_data=None):
        print("Entering Active State")

    def on_exit(self, event_data=None):
        print("Exiting Active State")

    def execute(self, event_data=None):
        print("Active state executing...")

class StateMachineNode(Node):
    def __init__(self):
        super().__init__('state_machine_node')
        # Create states
        idle_state = IdleState()
        active_state = ActiveState()
        
        # Create state machine
        self.sm = StateMachine(idle_state)
        # Add a simple transition that always fires (for demonstration)
        self.sm.add_transition(idle_state, Transition(active_state))
        
        # Set up a timer to trigger state machine execution periodically.
        self.timer = self.create_timer(2.0, self.timer_callback)

    def timer_callback(self):
        # Process an event and run the current state.
        self.sm.process_event()
        self.sm.run()

def main(args=None):
    rclpy.init(args=args)
    node = StateMachineNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
