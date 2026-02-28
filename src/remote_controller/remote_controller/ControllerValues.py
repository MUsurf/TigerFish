from numpy import float32

# temporary until there is a standard for this msg type
class ControllerValues:
    def __init__(self):
        self.x = float32(0)
        self.y = float32(0)
        self.z = float32(0)
        self.roll = float32(0)
        self.pitch = float32(0)
        self.yaw = float32(0)
    
    @classmethod
    def from_dict(cls, dict: dict):
        obj = cls()

        obj.x = float32(dict["x"])
        obj.y = float32(dict["y"])
        obj.z = float32(dict["z"])
        obj.roll = float32(dict["roll"])
        obj.pitch = float32(dict["pitch"])
        obj.yaw = float32(dict["yaw"])

        return obj
