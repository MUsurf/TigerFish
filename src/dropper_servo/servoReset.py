import time
from gpiozero import PWMOutputDevice

SERVO_PIN = 18
PWM_FREQUENCY = 50
MIN_DUTY_CYCLE = 2.5  # duty cycle % corresponding to angle 0 (min_angle)

WAIT_SECONDS = 2.0

pwm = PWMOutputDevice(SERVO_PIN, frequency=PWM_FREQUENCY)
pwm.value = MIN_DUTY_CYCLE / 100.0

time.sleep(WAIT_SECONDS)

pwm.close()