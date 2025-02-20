#!/usr/bin/env python3

# Begin typing imports
from typing import List
# End typing imports

# remove
from motor_command_local.motor_interface import MotorInterface
import time
# remove 
import threading

local_channels: List[int] = [x for x in range(8)]
num_motors: int = len(local_channels)
motor_caller = MotorInterface(local_channels, num_motors, 0, 100, .1, .5, 5)

num_motors = 8
high: List[int] = [20 for _ in range(num_motors)]
low: List[int] = [30 for _ in range(num_motors)]
list_thing = high
hl_counter = 0

def arm_motors():
    motor_caller.arm_seq()

arm_thread = threading.Thread(target=arm_motors, daemon=True)
arm_thread.start()

try:
    while (True):
        list_thing = high if hl_counter == 1 else low
        hl_counter = (hl_counter + 1) % 2
        motor_caller.callback(list_thing)
        time.sleep(5)
except KeyboardInterrupt:
    pass
finally:
    motor_caller.clo_seq()
    if arm_thread.is_alive():
        arm_thread.join(timeout=2)