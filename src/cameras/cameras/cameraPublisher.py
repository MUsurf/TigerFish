# https://www.youtube.com/watch?v=WhkiPYPIO9M

# Import OpenCV
import cv2

# Import ROS2 package modules/libraries
import rclpy
from sensor_msgs.msg import Image, CameraInfo
from camera_info_manager import CameraInfoManager
from rclpy.node import Node
from cv_bridge import CvBridge


class PublisherNodeClass(Node):
    def __init__(self):
        super().__init__("publisher_node")

        self.declare_parameter("camera_index", 0)
        idx = self.get_parameter("camera_index").value

        pi_pipeline = (
            f"libcamerasrc camera-name={idx} autofocus-mode=1 ! "
            "video/x-raw, width=800, height=600 ! "
            "videoconvert ! video/x-raw, format=BGR ! appsink"
        )

        self.get_logger().info("Attempting to open camera...")
        self.camera = cv2.VideoCapture(pi_pipeline, cv2.CAP_GSTREAMER)

        if not self.camera.isOpened():
            self.get_logger().warn(
                "Pi (3) camera does not work :'( Initiating a backup option :)"
            )
            self.camera = cv2.VideoCapture(idx)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        else:
            self.get_logger().info("Pi camera is set up!!")

        # CvBridge --> convert OpenCV images to publishable ROS2 messages
        self.bridgeObject = CvBridge()
        self.topicNameFrames = (
            "image_raw"  # Name of camera topic, must match in subscribers
        )
        self.queueSize = 20  # The queue size for messages

        # information for the calibration ####
        namespace = self.get_namespace().strip("/")
        self.camera_name = namespace if namespace else f"camera_{idx}"
        info_url = f"package://tiger_fish/config/{self.camera_name}_info.yaml"
        self.cinfo_manager = CameraInfoManager(
            self, cname=self.camera_name, url=info_url
        )
        self.info_publisher = self.create_publisher(
            CameraInfo, "camera_info", self.queueSize
        )
        # end calibration setup #####3#########

        self.publisher = self.create_publisher(
            Image, self.topicNameFrames, self.queueSize
        )

        self.periodCommunication = 0.04  # 25Hz

        # Timer that calls timer_callback function every comm period
        self.timer = self.create_timer(
            self.periodCommunication, self.timer_callbackFunction
        )

        # Counter tracking published images
        self.i = 0

    # Callback function called by Timer
    def timer_callbackFunction(self):

        # Read the frame using camera
        success, frame = self.camera.read()

        # Resize the image - note that this will really mess up calibration if resize is used
        # should set the hardware resolution instead
        # frame = cv2.resize(frame, (820, 640), interpolation=cv2.INTER_CUBIC)

        # Frame read success:
        if success:
            now = self.get_clock().now().to_msg()

            # Convert OpenCV frame --> ROS2 image msg
            ROS2ImageMessage = self.bridgeObject.cv2_to_imgmsg(frame, encoding="bgr8")
            ROS2ImageMessage.header.stamp = now
            ROS2ImageMessage.header.frame_id = f"{self.camera_name}_optical_frame"

            info_msg = self.cinfo_manager.get_camera_info()
            info_msg.header = ROS2ImageMessage.header

            # Publish the image
            self.publisher.publish(ROS2ImageMessage)
            self.info_publisher.publish(info_msg)

        # Use logger to display image msg on screen
        # self.get_logger().info("Publishing image number %d" % self.i)
        self.i += 1


# Main function; entry point
def main(args=None):
    # init rclpy
    rclpy.init(args=args)

    # Create publisher instance
    publisherObject = PublisherNodeClass()

    try:
        # Spin node; callback function called recursively
        rclpy.spin(publisherObject)
    except Exception:
        print("CameraPublisher spin failure.")

    # Destroy
    publisherObject.destroy_node()

    # Shutdown
    rclpy.shutdown()


if __name__ == "__main__":
    main()