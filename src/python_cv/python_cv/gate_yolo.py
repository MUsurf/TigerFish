import cv_bridge
import rclpy
from rclpy.node import Node
from ultralytics import YOLO

from sensor_msgs.msg import Image as RosImage
import numpy as np
from messages.msg import VisionMessage
import torch
import os
from ament_index_python.packages import get_package_share_directory


FRONT_LEFT_CAMERA_TOPIC = "?"
FRONT_RIGHT_CAMERA_TOPIC = "?"

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"


FREQ = 2 # HZ

def ros2_image_to_np_array(img : RosImage, bridge : cv_bridge.CvBridge):
    bgr = bridge.imgmsg_to_cv2(img, desired_encoding='bgr8')

    rgb_view = bgr[:, :, ::-1]   
    rgb = np.ascontiguousarray(rgb_view) 
    
    return rgb

def run_inference(model, image, conf_threshold = 0.25):
    results = model(image, verbose=False)[0]

    best = {
        0: None,
        1: None,
    }

    if results.boxes is None or len(results.boxes) == 0:
        return None, None

    boxes = results.boxes

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    classes = boxes.cls.cpu().numpy().astype(int)

    for box, conf, cls_id in zip(xyxy, confs, classes):
        if cls_id not in (0, 1):
            continue

        if conf < conf_threshold:
            continue

        x1, y1, x2, y2 = box

        cx = int(round((x1 + x2) / 2))
        cy = int(round((y1 + y2) / 2))

        if best[cls_id] is None or conf > best[cls_id][0]:
            best[cls_id] = (conf, (cx, cy))

    class_0_center = best[0][1] if best[0] is not None else None
    class_1_center = best[1][1] if best[1] is not None else None

    return class_0_center, class_1_center

class GateImageDetectionNode(Node):
    def __init__(self):
        super().__init__("gate_image_detection_node")
        
        pkg_share = get_package_share_directory('python_cv')
        DEFAULT_MODEL = os.path.join(pkg_share, 'models', 'gate_yolo.pt')

        self.survey_and_repair_left_publisher = self.create_publisher(VisionMessage, "survey_and_repair_gate_image_left", 10)
        self.survey_and_repair_right_publisher = self.create_publisher(VisionMessage, "survey_and_repair_gate_image_right", 10)
        self.search_and_rescue_left_publisher = self.create_publisher(VisionMessage, "search_and_rescue_gate_image_left", 10)
        self.search_and_rescue_right_publisher = self.create_publisher(VisionMessage, "search_and_rescue_gate_image_right", 10)
        
        self.left_camera_subscriber = self.create_subscription(RosImage, FRONT_LEFT_CAMERA_TOPIC, self.left_camera_cb)
        self.right_camera_subscriber = self.create_subscription(RosImage, FRONT_RIGHT_CAMERA_TOPIC, self.right_camera_cb)
        
        self.last_image_left : RosImage | None = None
        self.last_image_right : RosImage | None = None
        
        self.last_image_left_np : np.ndarray | None = None
        self.last_image_right_np : np.ndarray | None = None
        
        self.timer = self.create_timer(1.0 / FREQ, self.timer_cb)
        self.get_logger().info("Gate Image Detection node started")
        
        self.model = YOLO(DEFAULT_MODEL).to(DEVICE)
        self.cv_bridge = cv_bridge.CvBridge()

        
        

    def timer_cb(self):
        if self.last_image_left is None or self.last_image_right is None : return
        if self.last_image_left_np is None : self.last_image_left_np = ros2_image_to_np_array(self.last_image_left, self.cv_bridge)
        if self.last_image_right_np is None : self.last_image_right_np = ros2_image_to_np_array(self.last_image_right, self.cv_bridge)
        survey_and_repair_center_left, search_and_rescue_center_left = run_inference(self.model, self.last_image_left_np)
        survey_and_repair_center_right, search_and_rescue_center_right = run_inference(self.model, self.last_image_right_np)
        
        survey_and_repair_left_msg = VisionMessage()
        survey_and_repair_right_msg = VisionMessage()
        search_and_rescue_left_msg = VisionMessage()
        search_and_rescue_right_msg = VisionMessage()
        
        if survey_and_repair_center_left is not None :
            survey_and_repair_left_msg.x_position = survey_and_repair_center_left[0]
            survey_and_repair_left_msg.y_position = survey_and_repair_center_left[1]
            survey_and_repair_left_msg.is_detected = True
            # Not using confidence rn
        self.survey_and_repair_left_publisher.publish(survey_and_repair_left_msg)

        if survey_and_repair_center_right is not None :
            survey_and_repair_right_msg.x_position = survey_and_repair_center_right[0]
            survey_and_repair_right_msg.y_position = survey_and_repair_center_right[1]
            survey_and_repair_right_msg.is_detected = True
        self.survey_and_repair_right_publisher.publish(survey_and_repair_right_msg)

        if search_and_rescue_center_left is not None :
            search_and_rescue_left_msg.x_position = search_and_rescue_center_left[0]
            search_and_rescue_left_msg.y_position = search_and_rescue_center_left[1]
            search_and_rescue_left_msg.is_detected = True
        self.search_and_rescue_left_publisher.publish(search_and_rescue_left_msg)

        if search_and_rescue_center_right is not None :
            search_and_rescue_right_msg.x_position = search_and_rescue_center_right[0]
            search_and_rescue_right_msg.y_position = search_and_rescue_center_right[1]
            search_and_rescue_right_msg.is_detected = True
        self.search_and_rescue_right_publisher.publish(search_and_rescue_right_msg)
            
            

    def left_camera_cb(self, msg : RosImage):
        self.last_image_left = msg
        self.last_image_left_np = None
    
    def right_camera_cb(self, msg : RosImage):
        self.last_image_right = msg
        self.last_image_right_np = None
        


def main(args=None):
    rclpy.init(args=args)
    node = GateImageDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
