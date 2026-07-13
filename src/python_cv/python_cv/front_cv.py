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
from std_msgs.msg import Bool


FRONT_LEFT_CAMERA_TOPIC = "front_left_camera/image_raw"
FRONT_RIGHT_CAMERA_TOPIC = "front_right_camera/image_raw"

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

        cx = float(round((x1 + x2) / 2))
        cy = float(round((y1 + y2) / 2))

        if best[cls_id] is None or conf > best[cls_id][0]:
            best[cls_id] = (conf, (cx, cy))

    class_0_center = best[0][1] if best[0] is not None else None
    class_1_center = best[1][1] if best[1] is not None else None

    return class_0_center, class_1_center

class FrontImageDetectionNode(Node):
    def __init__(self):
        super().__init__("front_image_detection_node")
        
        pkg_share = get_package_share_directory('python_cv')
        DEFAULT_MODEL = os.path.join(pkg_share, 'models', 'gate_yolo.pt')
        TABLE_MODEL = os.path.join(pkg_share, 'models', 'table_yolo.pt')

        self.survey_and_repair_left_publisher_gate = self.create_publisher(VisionMessage, "survey_and_repair_gate_image_left_gate", 10)
        self.survey_and_repair_right_publisher_gate = self.create_publisher(VisionMessage, "survey_and_repair_gate_image_right_gate", 10)
        self.search_and_rescue_left_publisher_gate = self.create_publisher(VisionMessage, "search_and_rescue_gate_image_left_gate", 10)
        self.search_and_rescue_right_publisher_gate = self.create_publisher(VisionMessage, "search_and_rescue_gate_image_right_gate", 10)
        self.table_left_publisher = self.create_publisher(VisionMessage, "table_left", 10)
        self.table_right_publisher = self.create_publisher(VisionMessage, "table_right", 10)
        
        self.left_camera_subscriber = self.create_subscription(RosImage, FRONT_LEFT_CAMERA_TOPIC, self.left_camera_cb, 20)
        self.right_camera_subscriber = self.create_subscription(RosImage, FRONT_RIGHT_CAMERA_TOPIC, self.right_camera_cb, 20)
        self.gate_task_active_subscriber = self.create_subscription(Bool, 'gate_task_active', self.gate_task_active_subscriber_cb, 10)
        self.table_task_active_subscriber = self.create_subscription(Bool, 'table_task_active', self.table_task_active_subscriber_cb, 10)

        
        self.gate_task_active = True
        self.table_task_active = True
        self.last_image_left : RosImage | None = None
        self.last_image_right : RosImage | None = None
        
        self.last_image_left_np : np.ndarray | None = None
        self.last_image_right_np : np.ndarray | None = None
        
        self.timer = self.create_timer(1.0 / FREQ, self.timer_cb)
        self.get_logger().info("Gate Image Detection node started")
        
        self.model = YOLO(DEFAULT_MODEL).to(DEVICE)
        self.table_model = YOLO(TABLE_MODEL).to(DEVICE)
        self.cv_bridge = cv_bridge.CvBridge()

        
        

    def timer_cb(self):
        survey_and_repair_left_msg = VisionMessage()
        survey_and_repair_right_msg = VisionMessage()
        search_and_rescue_left_msg = VisionMessage()
        search_and_rescue_right_msg = VisionMessage()
        table_msg_left = VisionMessage()
        table_msg_right = VisionMessage()
        
        if self.last_image_left is not None and (self.gate_task_active or self.table_task_active):
            if self.last_image_left_np is None : self.last_image_left_np = ros2_image_to_np_array(self.last_image_left, self.cv_bridge)
            
            # Do gate state stuff
            if self.gate_task_active:
                survey_and_repair_center_left, search_and_rescue_center_left = run_inference(self.model, self.last_image_left_np)

                if survey_and_repair_center_left is not None :
                    survey_and_repair_left_msg.x_position = survey_and_repair_center_left[0]
                    survey_and_repair_left_msg.y_position = survey_and_repair_center_left[1]
                    survey_and_repair_left_msg.is_detected = True
                    # Not using confidence rn
                self.survey_and_repair_left_publisher_gate.publish(survey_and_repair_left_msg)
                
                if search_and_rescue_center_left is not None :
                    search_and_rescue_left_msg.x_position = search_and_rescue_center_left[0]
                    search_and_rescue_left_msg.y_position = search_and_rescue_center_left[1]
                    search_and_rescue_left_msg.is_detected = True
                self.search_and_rescue_left_publisher_gate.publish(search_and_rescue_left_msg)
                
            # Do table stuff
            if self.table_task_active:
                table, _ = run_inference(self.table_model, self.last_image_left_np)

                if table is not None :
                    table_msg_left.x_position = table[0]
                    table_msg_left.y_position = table[1]
                    table_msg_left.is_detected = True
                    # Not using confidence rn
                self.table_left_publisher.publish(table_msg_left)

        if self.last_image_right is not None and (self.gate_task_active or self.table_task_active):
            if self.last_image_right_np is None : self.last_image_right_np = ros2_image_to_np_array(self.last_image_right, self.cv_bridge)
            
            if self.gate_task_active:
                survey_and_repair_center_right, search_and_rescue_center_right = run_inference(self.model, self.last_image_right_np)

                if survey_and_repair_center_right is not None :
                    survey_and_repair_right_msg.x_position = survey_and_repair_center_right[0]
                    survey_and_repair_right_msg.y_position = survey_and_repair_center_right[1]
                    survey_and_repair_right_msg.is_detected = True
                self.survey_and_repair_right_publisher_gate.publish(survey_and_repair_right_msg)

                if search_and_rescue_center_right is not None :
                    search_and_rescue_right_msg.x_position = search_and_rescue_center_right[0]
                    search_and_rescue_right_msg.y_position = search_and_rescue_center_right[1]
                    search_and_rescue_right_msg.is_detected = True
                self.search_and_rescue_right_publisher_gate.publish(search_and_rescue_right_msg)
            
            if self.table_task_active:
                table, _ = run_inference(self.table_model, self.last_image_right_np)

                if table is not None :
                    table_msg_right.x_position = table[0]
                    table_msg_right.y_position = table[1]
                    table_msg_right.is_detected = True
                    # Not using confidence rn
                self.table_right_publisher.publish(table_msg_right)
            

    def gate_task_active_subscriber_cb(self, msg: Bool):
        self.gate_task_active = bool(msg.data)
        
    def table_task_active_subscriber_cb(self, msg: Bool):
        self.table_task_active = bool(msg.data)

    def left_camera_cb(self, msg : RosImage):
        self.last_image_left = msg
        self.last_image_left_np = None
    
    def right_camera_cb(self, msg : RosImage):
        self.last_image_right = msg
        self.last_image_right_np = None
        


def main(args=None):
    rclpy.init(args=args)
    node = FrontImageDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
