from werkzeug.serving import make_server
from threading import Thread

import rclpy

from remote_controller.remote_controller_node import RemoteControllerNode
from remote_controller.app import build_app

HOST = "0.0.0.0"
PORT = 5000

def main(args=None):
    rclpy.init(args=args)
    node = RemoteControllerNode()

    app = build_app(
        node.get_endpoints,
        node.post_endpoints
    )
    server = make_server(HOST, PORT, app)

    rclpy_thread = Thread(target = rclpy.spin, args=[node])
    flask_thread = Thread(target = server.serve_forever)

    try:
        node.get_logger().info("starting rclpy spinner thread")
        rclpy_thread.start()
        node.get_logger().info("starting flask server thread")
        flask_thread.start()

        rclpy_thread.join()
        flask_thread.join()
        
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down remote_controller node.")
    finally:
        node.destroy_node()
        server.shutdown()
        rclpy.shutdown()

if __name__ == "__main__":
    main()