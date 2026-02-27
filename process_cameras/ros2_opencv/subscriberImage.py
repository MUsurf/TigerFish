# https://www.youtube.com/watch?v=WhkiPYPIO9M

# Import OpenCV
import cv2
import os

# Import ROS2 package modules and libraries
import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from cv_bridge import CvBridge




class SubscriberNodeClass(Node):
    def __init__(self):
        # Init attributes of parent class
        super().__init__("subscriber_node")

        # Convert OpenCV images to ROS2 msgs
        self.bridgeObject = CvBridge()
        self.video_writer = None
        self.output_path = "/home/ros2_ws/src/output_images/processed_vid/processed_output.mp4"

        # Name must match publisher node
        self.topicNameFrames = "topic_camera_image"

        self.queueSize = 20

        # Create the subscriber (to types images, from topic, w/ queue size)
        self.subscription = self.create_subscription(
            Image, self.topicNameFrames, self.listener_callbackFunction, self.queueSize
        )
        self.subscription  # Prevent unused variable warning

    # Callback function that displays the recieved image
    def listener_callbackFunction(self, imageMessage):
        # Display msg to console
        self.get_logger().info("The image frame is received")

        # Convert ROS2 image msg to OpenCV image
        openCVImage = self.bridgeObject.imgmsg_to_cv2(imageMessage)

        # Show image on screen - only activate this for testing :)
        # cv2.imshow("Camera video", openCVImage)
        # cv2.waitKey(1)

        # this is initialization of a video writer to write video at 30 frames
        # in mp4v format! UwU
        if self.video_writer is None:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v') # mpv4 format initialization

            height, width = openCVImage.shape[:2]

            self.video_writer= cv2.VideoWriter(
                self.output_path,
                fourcc,
                30.0, # frames
                (width, height) # frame size
            )
        self.video_writer.write(openCVImage) # write the video


# Main function; entry point
def main(args=None):
    # init rclpy
    rclpy.init(args=args)

    # Create subscriber object
    subscriberNode = SubscriberNodeClass

    try:
        # Spin node, callback timer function is called recursively
        rclpy.spin(subscriberNode)
    except:
        print("CameraSubscriber spin failure.")

    # Destroy
    subscriberNode.destroy_node()

    # Shutdown
    rclpy.shutdown()


if __name__ == "__main__":
    main()
