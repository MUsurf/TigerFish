import time

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput

from yasmin import State, StateMachine, Blackboard
from yasmin_viewer import YasminViewerPub

from std_msgs.msg import Float32MultiArray, Float32, String, Bool 

from TigerFish.src.state_machine.src.PrequalMachine.gate_alignment import StartState 
from gate_alignment import GateAlignment
from go_through_gate import GoThroughGate
from pole_alignment import PoleAlignment
from tokyo_drift import TokyoDrift

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
        self.state_machine = StateMachine(outcomes={"complete"})
        
        # Create states
        # Utilize blackboards for data sharing between states and state machines.

        self.state_machine.add_state("GATE_ALIGNMENT", GateAlignment(self.pid_publisher), transitions={"next_state" : "GO_THROUGH_GATE"}) # Make Gate state work in both directions --> terminate on back through
        self.state_machine.add_state("GO_THROUGH_GATE", GoThroughGate(self.pid_publisher), transitions={"not_pole_danced" : "POLE_ALIGNMENT", "pole_danced" : "complete"})
        self.state_machine.add_state("POLE_ALIGNMENT", PoleAlignment(self.pid_publisher), transitions={"next_state" : "TOKYO_DRIFT"})
        self.state_machine.add_state("TOKYO_DRIFT", TokyoDrift(self.pid_publisher), transitions={"next_state" : "GATE_ALIGNMENT"})

        self.state_machine.set_start_state("GATE_ALIGNMENT")
    
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
            


        