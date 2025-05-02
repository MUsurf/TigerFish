class PID:
    """
    PID Controller Adapter Class
    This class provides an interface for controlling the PID controller.
    It exposes class methods to set target velocities or positions for six degrees of freedom (x, y, z, roll, pitch, yaw),
    as well as a method to stop the controller by resetting all targets to zero.
    Methods:
        setVelocity(x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
            Starts the PID controller with the specified velocity targets.
        setPosition(x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
            Starts the PID controller with the specified position targets.
        stop():
            Stops the PID controller by setting all position targets to zero.
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def setVelocity(cls, x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        """
        Starts the PID controller with the specified velocity.
        
        Args:
            x (float): The desired x velocity.
            y (float): The desired y velocity.
            z (float): The desired z velocity.
            roll (float): The desired roll velocity.
            pitch (float): The desired pitch velocity.
            yaw (float): The desired yaw velocity.
        """
        pass
    
    @classmethod
    def setPosition(cls, x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        """
        Starts the PID controller with the specified position.
        
        Args:
            x (float): The desired x position.
            y (float): The desired y position.
            z (float): The desired z position.
            roll (float): The desired roll position.
            pitch (float): The desired pitch position.
            yaw (float): The desired yaw position.
        """
        pass
    
    @classmethod
    def stop(cls):
        """Stops the PID controller."""
        cls.setPosition(0, 0, 0, 0, 0, 0)

class Camera:
    """
    Camera Adapter Class
    This class provides an interface for controlling the camera.
    It exposes class methods to check for gate visibility and alignment.
    Methods:
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def seeGate(cls) -> bool:
        """
        Checks if the gate is visible.
        
        Returns:
            bool: True if the gate is visible, False otherwise.
        """
        return False
    
    @classmethod
    def gateAlignedYaw(cls) -> bool:
        """
        Checks if the yaw is aligned to the gate.
        Yaw is aligned if the submarine is facing the gate.
        
        Returns:
            bool: True if aligned, False otherwise.
        """
        return False
    
    @classmethod
    def gateAlignedPosition(cls) -> bool:
        """
        Checks if the position is aligned to the gate.
        Position is aligned if the submarine is centering a half of the gate.
        
        Returns:
            bool: True if aligned, False otherwise.
        """
        return False
    
    @classmethod
    def gateAlignedDistance(cls) -> bool:
        """
        Checks if the distance to the gate is aligned.
        Distance is aligned if the submarine is within a certain distance (3m) of the gate.
        
        Returns:
            bool: True if aligned, False otherwise.
        """
        return False
    
    @classmethod
    def neededYaw(cls) -> float:
        """
        Gets the needed yaw to align with the gate.
        THIS MAY BE POSITION OR VELOCITY DEPENDING ON IMPLEMENTATION.
        
        Returns:
            float: The needed yaw angle.
        """
        return 0.0
    
    @classmethod
    def neededY(cls) -> float:
        """
        Gets the needed y position to align with the gate.
        THIS MAY BE POSITION OR VELOCITY DEPENDING ON IMPLEMENTATION.
        
        Returns:
            float: The needed y position.
        """
        return 0.0
    