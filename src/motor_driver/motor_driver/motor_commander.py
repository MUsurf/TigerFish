from board import SCL, SDA
import adafruit_pca9685 as PCA9685
import busio

i2c = busio.I2C(SCL, SDA)
pca = PCA9685.PCA9685(i2c, address=0x40)
pca.frequency = 50 
NUM_MOTORS = 8

MIN_WIDTH = 1100
MAX_WIDTH = 1900
MED_WIDTH = 1500

class MotorCommander():
    def __init__(self):
        self.motors : list = [pca.channels[channel] for channel in range(NUM_MOTORS)]
        
    def pulse_us_to_duty16(self, pulse_us) -> int:
        period_us = 1_000_000.0 / pca.frequency
        duty = pulse_us / period_us
        duty = max(0.0, min(1.0, duty))
        return int(round(duty * 65535))

    def set_motor_power(self, motor_power : float, motor_index : int, deadband : float = 0.0) -> int:
        if motor_index >= NUM_MOTORS or motor_index < 0: return None
        motor_power = max(-1.0, min(1.0, motor_power))
        
        if abs(motor_power) <= deadband : pulse_us = MED_WIDTH
        else : pulse_us = (MED_WIDTH + motor_power * (MED_WIDTH - MIN_WIDTH)) if motor_power < 0 else (MED_WIDTH + motor_power * (MAX_WIDTH - MED_WIDTH))
        
        duty = self.pulse_us_to_duty16(pulse_us)
        self.motors[motor_index].duty_cycle = duty
        return duty
    
    def set_motor_powers(self, motor_powers : list, deadband : float = 0.0) -> list:
        if len(motor_powers) != NUM_MOTORS:
            return None
        duty_list = [0 for _ in range(NUM_MOTORS)]
        for i, power in enumerate(motor_powers):
            duty_list[i] = self.set_motor_power(power, i, deadband)
        return duty_list
        