# Global info node/singleton
class Context:
    def __init__(self, node, pid_publisher):
        self.node = node
        self.pid_publisher = pid_publisher