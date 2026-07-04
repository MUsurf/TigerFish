import time
from yasmin import State, Blackboard
import numpy as np

class AlignYawGate(State):
    """
    Aligns the sub level to and facing the gate based on the position of the role images.

    Outcomes:
        next_state: goes to the align_role state
        reset: goes to reset state
        obtain_depth: goes to the obtain_depth state
        face_gate: goes back to the face_gate state
    """
    
    def __init__(self, context : dict) -> None:
        super().__init__(["end", "go_through_gate", "face_gate"])
        self.context = context
        self.role = "survey_and_repair"
        
        self.desired_depth = 0.75   # meters
        
        self.camera_distance = 0.1 # meters, not actual num
        self.image_distance = 0.1 # meters, not actual num
        
        self.stale_time : float | None = None
        self.max_stale_time : float = 1.0 # Seconds
        
        self.frequency = 15.0 # hz
        
    def direction_from_angles(self, x, y):
        return np.array([
            np.cos(y) * np.cos(x),
            np.cos(y) * np.sin(x),
            np.sin(y)
        ])
        
    def triangulate(self, x1, y1, x2, y2) -> np.ndarray:
        P1 = np.array([0.0, 0.0, 0.0])
        P2 = np.array([self.camera_distance, 0.0, 0.0])

        d1 = self.direction_from_angles(x1, y1)
        d2 = self.direction_from_angles(x2, y2)

        A = np.column_stack((d1, -d2))
        b = P2 - P1

        t, s = np.linalg.lstsq(A, b, rcond=None)[0]

        Q1 = P1 + t * d1
        Q2 = P2 + s * d2

        Q = (Q1 + Q2) / 2

        return Q
        
    def execute(self, bb : Blackboard):
        while True:
            st_t = time.time()
            left_detection_survey = bb.get("survey_and_repair_gate_image_left")
            right_detection_survey = bb.get("survey_and_repair_gate_image_right")
            left_detection_search = bb.get("search_and_rescue_gate_image_left")
            right_detection_search = bb.get("search_and_rescue_gate_image_right")
            detected = left_detection_survey[0] and right_detection_survey[1] and left_detection_search[2] and right_detection_search[3]
            
            if not detected:
                if not self.stale_time:
                    self.stale_time = time.time()
                elif time.time() - self.stale_time >= self.max_stale_time:
                    self.stale_time = None
                    return 'face_gate'
                time.sleep(max(0.0, (1.0 / self.frequency) - (time.time() - st_t)))
                continue 
            self.stale_time = None
            
            survey_loc = self.triangulate(
                left_detection_survey['x_posiiton'],
                left_detection_survey["y_position"],
                right_detection_survey['x_position'],
                right_detection_survey['y_position']
            )
            search_loc = self.triangulate(
                left_detection_search['x_position'],
                left_detection_search['y_position'],
                right_detection_search['x_position'],
                right_detection_search['y_position']
            )
            
            
            
            
                    
                
            
            

            