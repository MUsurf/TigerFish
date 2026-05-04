# Global info node/singleton
class Context:
    def __init__(self, node, pid_publisher):
        self.node = node
        self.pid_publisher = pid_publisher
        self.desired_depth = 2 # meters, 6.6 ft
        self.desired_width = 50
        self.screen_center = {100,100} # PLEASE CONFIRM
        self.pole_danced = False