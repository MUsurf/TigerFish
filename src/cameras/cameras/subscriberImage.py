# https://www.youtube.com/watch?v=WhkiPYPIO9M

# Import OpenCV
import cv2
import os

# Import ROS2 package modules and libraries
import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from cv_bridge import CvBridge
import rosbag2_py
from rclpy.serialization import serialize_message
import datetime


class SubscriberNodeClass(Node):
    def __init__(self):
        # Init attributes of parent class
        super().__init__("subscriber_node")
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        # Convert OpenCV images to ROS2 msgs
        self.bridgeObject = CvBridge()

        self.declare_parameter("record_type", "mp4")  # options: "mp4", "rosbag"
        self.record_type = self.get_parameter("record_type").value

        ns = self.get_namespace().strip("/")
        camera_name = ns if ns else "camera"

        self.base_dir = f"/home/tigerfish/TigerFish/videos/processed_vid/{camera_name}_records"
        os.makedirs(self.base_dir, exist_ok=True)

        self.bag_dir = os.path.join(self.base_dir, f"bag_{timestamp}")

        self.video_writer = None
        self.bag_writer = None

        if self.record_type == "rosbag":
            self.setup_rosbag()
            self.get_logger().info(f"recording to rosbag at {self.base_dir}")
        else:
            self.output_path = os.path.join(self.base_dir, f"{camera_name}_raw_log_{timestamp}.mp4") #mp4
            self.get_logger().info(f"recording to mp4 at {self.output_path}")

        # Name must match publisher node
        self.topicNameFrames = "image_raw"
        self.queueSize = 20

        # Create the subscriber (to types images, from topic, w/ queue size)
        self.subscription = self.create_subscription(
            Image, self.topicNameFrames, self.listener_callbackFunction, self.queueSize
        )
        self.subscription  # Prevent unused variable warning

    def setup_rosbag(self):
        self.bag_writer = rosbag2_py.SequentialWriter()
        storage_option = rosbag2_py.StorageOptions(uri=self.bag_dir, storage_id="mcap")

        converter_options = rosbag2_py.ConverterOptions("", "")
        self.bag_writer.open(storage_option, converter_options)

        topic_info = rosbag2_py.TopicMetadata(
            name="image_raw",
            type="sensor_msgs/msg/Image",
            serialization_format="cdr",
            id=0,
        )

        self.bag_writer.create_topic(topic_info)

    # Callback function that writes the recieved image
    def listener_callbackFunction(self, imageMessage):
        # Display msg to console
        # self.get_logger().info("The image frame is received")

        if self.record_type == "rosbag":
            self.bag_writer.write(
                "image_raw",
                serialize_message(imageMessage),
                imageMessage.header.stamp.sec * 10**9
                + imageMessage.header.stamp.nanosec,
            )
        else:
            # Convert ROS2 image msg to OpenCV image
            openCVImage = self.bridgeObject.imgmsg_to_cv2(
                imageMessage, desired_encoding="bgr8"
            )

            # Show image on screen - only activate this for testing :)
            # cv2.imshow("Camera video", openCVImage)
            # cv2.waitKey(1)

            # this is initialization of a video writer to write video at 30 frames
            # in mp4v format! UwU
            if self.video_writer is None:
                os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
                # Use a software encoder that is more likely to work inside container
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # software mp4v codec
                height, width = openCVImage.shape[:2]

                self.video_writer = cv2.VideoWriter(
                    self.output_path,
                    fourcc,
                    25.0,  # frames
                    (width, height),  # frame size
                )
                
                self.get_logger().info(f"Absolute path: {os.path.abspath(self.output_path)}")
                self.get_logger().info(f"VideoWriter initialized at {width}x{height}")


            self.video_writer.write(openCVImage)  # write the video

    def destroy_node(self):
        if self.video_writer is not None:
            self.get_logger().info("Releasing Video writer")
            self.video_writer.release()
        if self.bag_writer is not None:
            self.get_logger().info("Closing ROS Bag...")
            del self.bag_writer
        super().destroy_node()


# Main function; entry point
def main(args=None):
    # init rclpy
    rclpy.init(args=args)

    # Create subscriber object
    subscriberNode = SubscriberNodeClass()

    try:
        # Spin node, callback timer function is called recursively
        rclpy.spin(subscriberNode)
    except Exception:
        print("CameraSubscriber spin failure.")
    except KeyboardInterrupt:
        subscriberNode.get_logger().info("KeyboardInterrupt received (Ctrl+C)")   
    finally:
        subscriberNode.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
