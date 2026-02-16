# Begin typing imports
from typing import List
import threading
# End typing imports

# Begin imports
import busio
from board import SCL, SDA
import adafruit_pca9685 as PCA9685
# End imports

# BEGIN SETUP
i2c = busio.I2C(SCL, SDA)
pca = PCA9685.PCA9685(i2c, address=0x40)
pca.frequency = 400  # Hz, works with BLHeli_32 PWM mode
NUM_MOTORS = 8
# END SETUP

def threaded(fn):
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class MotorCommand():
    def __init__(self, 
        update_frequency: float,
        delta_limit: float,
        ) -> None:
        self.update_frequency: float = update_frequency
        self.delta_limit: float = delta_limit

        self.step_size: float = delta_limit / update_frequency

        self.pin_states: List[float] = [0 for _ in range(NUM_MOTORS)]
        self.pin_targets: List[float] = [0 for _ in range(NUM_MOTORS)]


        self.motors: List[PCA9685.PWMChannel] = [
            pca.channels[channel] for channel in range(NUM_MOTORS)]
        
        self.stop_event = threading.Event()
        self.motor_thread = self.motor_update_loop()

    def _percent_drive_to_duty(self, percent_drive: float) -> int:

        # Map 0-100% speed to 1000-2000 us pulse for BLHeli_32
        micro_sec = int(1000 + int((percent_drive + 100) * 5))

        """Convert Microsecond pulses to duty cycle for PCA9685"""
        samp_time: float = (1 / pca.frequency) * 1_000_000  # microseconds per cycle
        duty_cycle = int((65536 * micro_sec) / samp_time)
        return duty_cycle
    

    def set_motor_speed(self, motor_index: int, speed: float) -> float:
        '''Set the speed of a single motor (-100 - 100) compatible with BLHeli_32'''

        pwm_value = self._percent_drive_to_duty(speed)
        self.motors[motor_index].duty_cycle = pwm_value
        return pwm_value
    
    @threaded
    def motor_update_loop(self):
        """Continuously update motors toward target speeds"""
        while self.stop_event.is_set() == False:
            self.motor_step()
            if self.stop_event.wait(timeout = 1.0 / self.update_frequency):
                break
        

    def motor_step(self, targets: List[float] = None):
        """Move pin towards target supplied"""
        
        if targets is None:
            targets = self.pin_targets

        directions: List[float] = self._targetDistance(targets)
        for index in range(len(directions)):
            if directions[index] == 0:
                continue

            # Update pinState toward target, avoiding overshoot
            delta = directions[index] * self.step_size
            if abs(delta) >= abs(targets[index] - self.pin_states[index]):
                self.pin_states[index] = targets[index]
            else:
                self.pin_states[index] += delta

        return self.set_motors(self.pinStates)


    def set_motors(self, speeds: List[float]) -> List[float]:
        """Sets pins to values given by speed position"""
        pwm_values = []
        for index in range(self.motorNum):
            # Clamp speed to 0-100 before sending
            clamped_speed = max(0, min(100, speeds[index]))
            pwm_values.append(self.set_motor_speed(index, clamped_speed))
        return pwm_values

    def _targetDistance(self, targets: List[float]) -> List[float]:
        """Figures out which direction to step pins"""

        values: List[float] = [target - pinState for target, pinState in zip(targets, self.pinStates)]
        conversions: List[float] = [float(value / abs(value)) if value != 0 else 0 for value in values]
        return conversions
    
    def set_targets(self, targets: List[float]) -> None:
        """Sets new target speeds for motors"""
        self.pin_targets = targets

