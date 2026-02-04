# https://www.youtube.com/watch?v=WhkiPYPIO9M

# Import OpenCV
import cv2

# Import ROS2 package modules and libraries
import rclpy
from sensor_msgs.msg import Image
from rclpy.node import Node
from cv_bridge import CvBridge

class SubscriberNodeClass(Node):

	def __init__(self):
		# Init attributes of parent class
		super().__init__('subscriber_node')
		
		# Convert OpenCV images to ROS2 msgs
		self.bridgeObject = CvBridge()
		
		# Name must match publisher node
		self.topicNameFrames='topic_camera_image'
		
		self.queueSize = 20
		
		# Create the subscriber (to types images, from topic, w/ queue size)
		self.subscription = self.create_subscription(Image, self.topicNameFrames, self.listener_callbackFunction, self.queueSize)
		self.subscription # Prevent unused variable warning
		
	# Callback function that displays the recieved image
	def listener_callbackFunction(self, imageMessage):
		# Display msg to console
		self.get_logger().info('The image frame is received')
		
		# Convert ROS2 image msg to OpenCV image
		openCVImage = self.bridgeObject.imgmsg_to_cv2(imageMessage)
		
		# Show image on screen
		cv2.imshow("Camera video", openCVImage)
		cv2.waitKey(1)
		
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
	
if __name__ == '__main__':
	main()
		
		
