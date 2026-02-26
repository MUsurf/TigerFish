# https://www.youtube.com/watch?v=WhkiPYPIO9M

# Import OpenCV
import cv2

# Import ROS2 package modules/libraries
import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from cv_bridge import CvBridge


class PublisherNodeClass(Node):
    def __init__(self):
        super().__init__("publisher_node")

    # Create an instance of OpenCV VideoCapture Obj
    self.cameraDeviceNumber = 0
    self.camera = cv2.VideoCapture(self.cameraDeviceNumber)

    # CvBridge --> convert OpenCV images to publishable ROS2 messages
    self.bridgeObject = CvBridge()

    # Name of camera topic, must match in subscribers
    self.topicNameFrames = "topic_camera_image"

    # The queue size for messages
    self.queueSize = 20

    self.create_publisher(Image, self.topicNameFrames, self.queueSize)

    self.periodCommunication = 0.02  # seconds

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
        # Resize the image
        frame = cv2.resize(frame, (820, 640), interpolation=cv2.INTER_CUBIC)

        # Frame read success:
        if success == True:
            # Convert OpenCV frame --> ROS2 image msg
            ROS2ImageMessage = self.bridgeObject.ccv2_to_imgmsg(frame)
            # Publish the image
            self.publisher.publish(ROS2ImageMessage)

        # Use logger to display image msg on screen
        self.get_logger().info("Publishing image number %d" % self.i)
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
    except:
        print("CameraPublisher spin failure.")

    # Destroy
    publisherObject.destroy_node()

    # Shutdown
    rclpy.shutdown()

    if __name__ == "__main__":
        main()
