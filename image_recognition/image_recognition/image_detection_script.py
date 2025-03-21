import cv2 as cv
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from geometry_msgs.msg import Pose, PoseArray

# Constants
POSE_ARRAY_PUBLISHER = 'positions'
IMAGE_SUBSCRIPTION = 'image_topic'
LOWER_COLOR = np.array([0, 150, 150])
UPPER_COLOR = np.array([30, 255, 255])
MORPH_KERNEL = np.ones((15, 15), np.uint8)

# Script to get a direction from a orange oblong
# Uses opencv to process the image and get a "direction"
# Currently only supports a single direction averaging the oblong

# Set up node stuff
class imageDetectionPkg(Node): 
    def __init__(self):
        super().__init__('image_detection_node')

        # Create a publisher for the detected angle
        self.publisher_= self.create_publisher(PoseArray, POSE_ARRAY_PUBLISHER, 10)

        # Create a subscriber to the image topic
        self.subscription = self.create_subscription(
            Image, IMAGE_SUBSCRIPTION, self.imageDetection, 10)

        # Initialize CvBridge for image conversion
        self.bridge = CvBridge()

        self.get_logger().info('image detection node has been started')

    def imageDetection(self, msg):
        """Callback function for processing incoming images."""

        try:
            frame = self.bridge.imgmsg_to_cv2(msg)
        except Exception as e:
            self.get_logger().error(f"Error converting image: {e}")
            return

        # Flip frame horizontally
        frame = cv.flip(frame, 1)

        # Convert BGR to HSV
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        # Define range of orange color in HSV
        lower_color = LOWER_COLOR
        upper_color = UPPER_COLOR

        # Threshold the HSV image to get only orange colors
        mask = cv.inRange(hsv, lower_color, upper_color)

        kernel = MORPH_KERNEL
        mask_smoothed = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

        # Look for any contours
        contours, _ = cv.findContours(mask_smoothed, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # If any contours:
        if contours:
        # Get the largest contour found as this is likely the wanted shape
            largest_contour = max(contours, key=cv.contourArea)
            
            try:
                # Get the convex hull of a point set to detect angle point
                hull = cv.convexHull(largest_contour,returnPoints = False)
                # Get all the examples of convexity
                defects = cv.convexityDefects(largest_contour,hull)
                
                # We want to keep the furthest point so track params
                maxDefect = [0,0,0,0]
                
                # If there are defects
                if(defects is not None):
                    # For all defects (convex points)
                    for i in range(defects.shape[0]):
                        # Get relevant points [start, end, far, distance]
                        # start: index (of start of line of convexity),
                        # end: index (of end of line with convexity),
                        # far: convex point,
                        # distance: distance of far from line of convexity
                        test = defects[i,0]

                        # If distance is greater than current max
                        if(test[3] > maxDefect[3]):
                            ## far = tuple(largest_contour[test[2]][0])
                            # Update max to new largest
                            maxDefect = test 
                    
                    
                    # Get the relevant points for the start, end, and far point
                    start = tuple(largest_contour[maxDefect[0]][0])
                    end = tuple(largest_contour[maxDefect[1]][0])
                    mid = tuple(largest_contour[maxDefect[2]][0])
                
                    
                    # Publish the points
                    # Use a PoseArray which allows multiple poses
                    msg = PoseArray()
                    msg.header.stamp = self.get_clock().now().to_msg()

                    # Each pose will be used as an x,y 2D point
                    start_pose = Pose()
                    mid_pose = Pose()
                    end_pose = Pose()

                    # Set the positions of the 3 poses
                    start_pose.position.x = float(start[0])
                    start_pose.position.y = float(start[1])
                    start_pose.position.z = 0.0
                    mid_pose.position.x = float(mid[0])
                    mid_pose.position.y = float(mid[1])
                    mid_pose.position.z = 0.0
                    end_pose.position.x = float(end[0])
                    end_pose.position.y = float(end[1])
                    end_pose.position.z = 0.0

                    # Add the poses to the message
                    msg.poses = [start_pose, mid_pose, end_pose]
                    self.publisher_.publish(msg)


                    self.get_logger().info(f"Published positions: {start}, {mid}, {end}")

            # If error from opencv then skip this frame
            except cv.error:
                self.get_logger().error("Error processing contours")
                return


def main(args = None):
    rclpy.init(args=args)
    node = imageDetectionPkg()
    rclpy.spin(node)
    rclpy.shutdown()