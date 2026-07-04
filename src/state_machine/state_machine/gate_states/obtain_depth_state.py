import time
import yasmin
from yasmin import State, Blackboard
from messages.msg import PIDInput

class ObtainDepth(State):
    """
    Achieves and  maintains the desired depth of the sub.
    When transitioning to this state, prev state pushes its name to blackboard \"prev_state\" for return.

    Outcomes:
        Goes to whatever previous state it came from.
    """
    
    def __init__(self, context : dict) -> None:
        super().__init__(["face_gate", "end"])
        self.context : dict = context
        self.desired_depth : float = 0.75   # meters
        self.depth_range : float = 0.15     # meters
        self.maintain_time : float = 3.0    # sec
        
        self.depth_time : float | None = None
        
        self.above_water_threshold = -0.05
        
        self.frequency = 10.0 # Hz
        self.start_yaw = None
        
    def execute(self, bb : Blackboard):
        yasmin.YASMIN_LOG_INFO("Executing state Obtain Depth")
        
        while True:
            st_t = time.time()
            odom = bb.get("odom")
            depth = bb.get("depth")
            
            if self.start_yaw is None : self.start_yaw = odom["yaw"]
            if (depth >= self.above_water_threshold) : return "end"

            err = abs(depth - self.desired_depth)            
            if err >= self.depth_range:
                self.depth_time = None
            else:
                if self.depth_time is None : 
                    self.depth_time = time.time()
                else:
                    elapsed = time.time() - self.depth_time
                    if elapsed >= self.maintain_time:
                        return "face_gate"
                    
            msg = PIDInput() 
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = True
            msg.z_measurement = depth 
            msg.z_setpoint = self.desired_depth
            msg.yaw_setpoint = self.start_yaw
            msg.measurement_yaw = odom["yaw"]
            msg.pitch_setpoint = 0.0
            msg.measurement_pitch = odom["pitch"]
            msg.roll_setpoint = 0.0
            msg.measurement_roll = odom["roll"]
            self.context.pid_publisher.publish(msg)

            time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))