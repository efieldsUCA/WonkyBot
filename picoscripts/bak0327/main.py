"""
Rename this file to main.py
"""

import sys
from utime import ticks_us, ticks_diff
import select
from machine import freq
from mobile_control.diff_drive_controller import DiffDriveController

# SETUP
# Overclock
freq(240_000_000)  # Pico2 original: 150_000_000
# Instantiate robot
mobile_base = DiffDriveController(
    left_ids=((16, 17, 18), (26, 27)), right_ids=((21, 20, 19), (6, 7))
)
pico_messenger = select.poll()  # create a poll object
pico_messenger.register(sys.stdin, select.POLLIN)  # peek at serial port input
# Constants
tx_period_us = 16_667  # 60Hz
# Variables
targ_lin_vel, targ_ang_vel = 0.0, 0.0
step_dir = 0
last_us = ticks_us()
# print("Pico is ready...")  # debug

# LOOP
while True:
    # Transmit data (TX)
    now_us = ticks_us()
    if ticks_diff(now_us, last_us) >= tx_period_us:
        meas_lin_vel, meas_ang_vel = mobile_base.get_vels()
        out_msg = f"{meas_lin_vel:.3f},{meas_ang_vel:.3f}"
        print(out_msg)  # main.py will send this to computer
        last_us = now_us  # update last time stamp
    # Receive data (RX)
    is_waiting = pico_messenger.poll(0)  # check data in USB
    if is_waiting:
        in_msg = sys.stdin.readline().strip()  # take out whitespaces
        targ_vels = in_msg.split(",")  # get a list
        if len(targ_vels) == 2:
            targ_lin_vel = float(targ_vels[0])
            targ_ang_vel = float(targ_vels[1])
            mobile_base.set_vels(targ_lin_vel, targ_ang_vel)
