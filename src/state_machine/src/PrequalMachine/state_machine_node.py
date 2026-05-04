import math

import rclpy
from rclpy import Node

from nav_msgs.msg import Odometry
from messages.msg import PIDInput

from yasmin import State, StateMachine, Blackboard
from yasmin_viewer import YasminViewerPub

from std_msgs.msg import Float32MultiArray, Float32, String, Bool 

from tf_transformations import euler_from_quaternion
 
from gate_alignment import GateAlignment
from go_through_gate import GoThroughGate
from pole_alignment import PoleAlignment
from tokyo_drift import TokyoDrift
from reset_state import ResetState
from context import Context

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
        
        # Create blackboard
        self.blackboard = Blackboard()
        
        # Create context instance
        self.context = Context(self, self.pid_publisher)

        # Create state machine
        self.state_machine = StateMachine(outcomes={"complete"})
        
        # Create states
        self.state_machine.add_state("GATE_ALIGNMENT", GateAlignment(self.context), transitions={"next_state" : "GO_THROUGH_GATE", "reset" : "RESET"}) # Make Gate state work in both directions --> terminate on back through
        self.state_machine.add_state("GO_THROUGH_GATE", GoThroughGate(self.context), transitions={"next_state" : "POLE_ALIGNMENT", "pole_danced" : "complete", "reset" : "RESET"})
        self.state_machine.add_state("POLE_ALIGNMENT", PoleAlignment(self.context), transitions={"next_state" : "TOKYO_DRIFT", "reset" : "RESET"})
        self.state_machine.add_state("TOKYO_DRIFT", TokyoDrift(self.context), transitions={"next_state" : "GATE_ALIGNMENT", "reset" : "RESET"})
        self.state_machine.add_state("RESET", ResetState(self.context), transitions={"next_state" : "GATE_ALIGNMENT"})

        # Set up state machine
        self.state_machine.set_start_state("GATE_ALIGNMENT")
    
        self.yasmin_pub = YasminViewerPub(self.state_machine, "TigerFish_SM")

        self.timer = self.create_timer(0.1, self.state_machine)

        self.get_logger().info("State machine initialized successfully!")
        
    
    
    # Call back functions keep blackboard up to date with ROS topics
    def gate_cb(self, msg):
        self.blackboard["gate_detection"] = { # Utilize blackboard for data sharing between states and state machines.
            "seen": msg.z,
            "yaw_angle": msg.x,
            "pitch_angle": msg.y,
        }

    def pole_cb(self, msg):
        self.blackboard["pole_detection"] = {
            "seen": msg.z,
            "yaw_angle": msg.x,
            "pitch_angle": msg.y,
            "pixel_width": msg.width,
    }

    def _odom_cb(self, msg):
        # x = msg.pose.pose.position.x
        # y = msg.pose.pose.position.y
        
        # Orientation Quaternion
        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        
        orientation_list = [qx, qy, qz, qw]
        (roll, pitch, yaw) = euler_from_quaternion(orientation_list)
        
        self.blackboard["odom"] = {
            # "x": x,
            # "y": y,
            "qx": qx,
            "qy": qy,
            "qz": qz,
            "qw": qw,
            "yaw": math.degrees(yaw),
            "pitch": math.degrees(pitch),
            "roll": math.degrees(roll),                
        }

    def depth_sensor_cb(self, msg):
        self.blackboard["depth"] = msg.data
            


        