import time

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput

from yasmin import State, StateMachine, Blackboard
from yasmin_viewer import YasminViewerPub

from std_msgs.msg import Float32MultiArray, Float32, String, Bool 

from start_state import StartState 
from enter_gate_state import EnterGateState
from to_pole_state import ToPoleState
from circle_pole_state import CirclePoleState
from from_pole_state import FromPoleState
from end_gate_state import EndGateState
from complete_state import Complete

# Global info node/singleton
class Context:
    def __init__(self, node, pid_publisher):
        self.node = node
        self.pid_publisher = pid_publisher

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
        
        self.context = Context(pid_publisher)

        # Create state machine
        self.state_machine = StateMachine(outcomes={"COMPLETE"})
        
        # Create states
        # Utilize blackboards for data sharing between states and state machines.

        self.state_machine.add_state("START_STATE", StartState(), transitions={"next_state" : "START_GATE_STATE"})
        self.state_machine.add_state("ENTER_GATE_STATE", EnterGateState(self.pid_publisher), transitions={"next_state" : "TO_POLE_STATE"}) # Make Gate state work in both directions --> terminate on back through
        self.state_machine.add_state("TO_POLE_STATE", ToPoleState(self.pid_publisher), transitions={"next_state" : "CIRCLE_POLE_STATE"})
        self.state_machine.add_state("CIRCLE_POLE_STATE", CirclePoleState(self.pid_publisher), transitions={"next_state" : "TO_POLE_STATE"})
        self.state_machine.add_state("FROM_POLE_STATE", FromPoleState(self.pid_publisher), transitions={"next_state" : "END_GATE_STATE"})
        self.state_machine.add_state("END_GATE_STATE", EndGateState(self.pid_publisher), transitions={"next_state" : "COMPLETE"})
        self.state_machine.add_state("COMPLETE", Complete())

        self.state_machine.set_start_state("START_STATE")
    
        self.yasmin_pub = YasminViewerPub(self.state_machine, "TigerFish_SM")

        self.timer = self.create_timer(0.1, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")
        
        # To run the statemachine, create a StateMachine and Blackboard, then run StateMachine(Blackboard) (?)
        
    def gate_cb(self, msg):
        self.blackboard["gate_detection"] = {
            "seen": msg.does_see,
            "x": msg.x_pos,
            "y": msg.y_pos,
        }

    def _odom_cb(self, msg):
        self.blackboard["odom"] = msg

    def depth_sensor_cb(self, msg):
        self.blackboard["depth"] = msg.data
            


        