import time
import yasmin
from yasmin import State, Blackboard
from messages.msg import PIDInput, VisionMessage

class FaceGate(State):
    """
    Aligns the sub level to and facing the gate based on the position of the role images.

    Outcomes:
        next_state: goes to the align_gate state
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
    """
    
    def __init__(self, context : dict) -> None:
        super().__init__(["align_gate", "end"])
        self.context : dict = context
        
        self.detection_threshold : float = 0.8 # 80% of past 10 frames must contain all. 
        self.past_detections : list[tuple[bool, bool, bool, bool]] = [(False, False) for _ in range(10)]
        self.desired_depth = 0.75   # meters
        self.above_water_threshold = -0.05
        
        self.frequency = 10.0 # Hz
        
    def get_detection_amount(self) -> float:
        seen = 0
        for t in self.past_detections:
            seen += 1 if (t[0] and t[1] and t[2] and t[3]) else 0
        return seen / len(self.past_detections)
    
    def push_detection(self, detected : tuple[bool, bool, bool, bool]) -> None:
        self.past_detections.insert(0, detected)
        self.past_detections.pop()
        
    def execute(self, bb : Blackboard):
        """
        Executes the logic for the gate alignment starting state

        Returns: next_state
        """
        yasmin.YASMIN_LOG_INFO("Executing state Gate Alignment")
        
        self.past_detections = [(False, False) for _ in range(10)]

        while True:
            st_t = time.time()
            # Get blackboard info
            left_detection_survey = bb.get("survey_and_repair_gate_image_left")
            right_detection_survey = bb.get("survey_and_repair_gate_image_right")
            left_detection_search = bb.get("search_and_rescue_gate_image_left")
            right_detection_search = bb.get("search_and_rescue_gate_image_right")
            odom = bb.get("odom")
            depth = bb.get("depth")        
            
            if (depth <= self.above_water_threshold):
                return "end"
                
            detections = (
                left_detection_survey['is_detected'], 
                right_detection_survey['is_detected'], 
                left_detection_search['is_detected'], 
                right_detection_search['is_detected'])
            detected = detections[0] and detections[1] and detections[2] and detections[3]
            self.push_detection(detections)
            if self.get_detection_amount >= self.detection_threshold:
                return 'align_gate'
            
            yaw_power = 0.0 if detected else 0.1
                        
            msg = PIDInput()
            msg.z_mode = True
            msg.roll_mode = True
            msg.pitch_mode = True
            msg.yaw_mode = False
            msg.yaw_power = yaw_power
            msg.z_measurement = depth 
            msg.z_setpoint = self.desired_depth
            msg.pitch_setpoint = 0.0
            msg.measurement_pitch = odom["pitch"]
            msg.roll_setpoint = 0.0
            msg.measurement_roll = odom["roll"]
            self.context.pid_publisher.publish(msg)

            time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))
        

     
        
    