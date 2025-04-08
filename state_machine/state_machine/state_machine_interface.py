# state_machine_interface.py

from abc import ABC, abstractmethod

class State(ABC):
    """Abstract base class representing a state in the state machine."""

    @abstractmethod
    def on_entry(self, event_data=None):
        """
        This method is called when the state is entered.
        Subclasses should override this to include entry behavior.
        """
        pass

    @abstractmethod
    def on_exit(self, event_data=None):
        """
        This method is called when exiting the state.
        Subclasses should override this to include cleanup behavior.
        """
        pass

    @abstractmethod
    def execute(self, event_data=None):
        """
        The main execution callback that is invoked (possibly repeatedly) 
        while the state is active.
        """
        pass


class Transition:
    """
    A stub for state transitions. A transition has:
      - A target state (a subclass of State)
      - A condition function that determines if the transition should trigger.
    """
    def __init__(self, target_state: State, condition=None):
        self.target_state = target_state
        # The condition is a function that takes event data and returns a boolean.
        # If no condition is provided, the transition always fires.
        self.condition = condition or (lambda event: True)

    def is_triggered(self, event_data=None):
        """
        Check if the transition condition is met.
        """
        return self.condition(event_data)


class StateMachine:
    """
    A simple state machine controller.
    """
    def __init__(self, initial_state: State):
        self.current_state = initial_state
        self.transitions = {}  # Map current_state -> list of Transition instances

    def add_transition(self, state: State, transition: Transition):
        """
        Register a transition for a given state.
        """
        if state not in self.transitions:
            self.transitions[state] = []
        self.transitions[state].append(transition)

    def process_event(self, event_data=None):
        """
        Process an event: check for any valid transitions from the current state.
        """
        transitions = self.transitions.get(self.current_state, [])
        for transition in transitions:
            if transition.is_triggered(event_data):
                self.current_state.on_exit(event_data)
                self.current_state = transition.target_state
                self.current_state.on_entry(event_data)
                break  # Only trigger one transition per event cycle

    def run(self, event_data=None):
        """
        Run the current state's execution logic.
        """
        self.current_state.execute(event_data)
