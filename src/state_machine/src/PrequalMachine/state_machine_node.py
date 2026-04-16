import time

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput

from yasmin import State, StateMachine
from yasmin_viewer import YasminViewerPub

from std_msgs.msg import Float32MultiArray, Float32, String, Bool 

from start_state import StartState 
from gate_state import GateState
from to_pole_state import ToPoleState
from circle_pole_state import CirclePoleState
from from_pole_state import FromPoleState

class StateMachineNode(Node): 
    def __init__(self):
        super().__init__("state_machine_node")

        # Create ROS subscribers
        self.gate_image_subscriber = self.create_subscription(
            ImageInfoMsg, "gate_detection_topic", self.gate_cb, 10  # ImageInfoMsg format: bool does_see; float x_pos; float y_pos;
        )
        
        self.pole_image_subscriber = self.create_subscription(
            ImageInfoMsg, "pole_detection_topic", self.pole_cb, 10
        )
        
        self.orientation_subscriber = self.create_subscription( # IMU?
            Odometry, "state_estimation", self._odom_cb, 10
        )
        
        self.depth_sensor_subscriber = self.create_subscription(
            Float32, "depth", self.depth_sensor_cb, 10
        )
        
        self.pid_publisher = self.create_publisher(PIDInput, "pid_input", 10)

        # Create state machine
        self.state_machine = StateMachine(outcomes={"complete"})
        
        # Create states
        # Utilize blackboards for data sharing between states and state machines.
        # TODO: INSTEAD OF PASSING PUBLISHERS, MAKE A SINGLETON CLASS FOR VARIABLES THAT COME FROM PIBLISHERS; PASS THAT
        self.state_machine.add_state("START_STATE", StartState(), transitions={"next_state" : "GATE_STATE"})
        self.state_machine.add_state("GATE_STATE", GateState(self.pid_publisher), transitions={"next_state" : "TO_POLE_STATE"}) # Make Gate state work in both directions --> terminate on back through
        self.state_machine.add_state("TO_POLE_STATE", ToPoleState(self.pid_publisher), transitions={"next_state" : "CIRCLE_POLE_STATE"})
        self.state_machine.add_state("CIRCLE_POLE_STATE", CirclePoleState(self.pid_publisher), transitions={"next_state" : "FROM_POLE_STATE"})
        self.state_machine.add_state("FROM_POLE_STATE", FromPoleState(self.pid_publisher), transitions={"next_state" : "GATE_STATE"})

        self.state_machine.set_start_state("START_STATE")
    
        self.yasmin_pub = YasminViewerPub(self.state_machine, "TigerFish_SM")

        self.timer = self.create_timer(0.1, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")
