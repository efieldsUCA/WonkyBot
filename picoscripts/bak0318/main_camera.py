import sys
import select
from machine import Pin, freq
from utime import ticks_us
from diff_drive_controller import DiffDriveController

# -------- SETUP --------
freq(240_000_000)

# Drivetrain Configuration
ddc = DiffDriveController(
    left_ids=((3, 2, 4), (21, 20)),
    right_ids=((6, 7, 8), (11, 10)), 
)

ol = Pin("WL_GPIO0", Pin.OUT)

in_msg_poll = select.poll()
in_msg_poll.register(sys.stdin, select.POLLIN)

tic = ticks_us()

# -------- LOOP --------
print("Pico Serial Listener Active (Drive & Stop Ready)...")

while True:
    # 1. Read commands from the Pi
    if in_msg_poll.poll(0):
        line = sys.stdin.readline().strip()
        buffer = line.split(",")
        
        # Original 4-part manual override
        if len(buffer) == 4:
            try:
                targ_lin_vel = float(buffer[0])
                targ_ang_vel = float(buffer[1])
                ddc.set_vels(targ_lin_vel, targ_ang_vel)
            except ValueError:
                pass
                
        # ROS 2 Vision commands
        elif len(buffer) == 3:
            cmd = buffer[0]
            
            try:
                lin = float(buffer[1])
                ang = float(buffer[2])
                
                if cmd == "DRIVE":
                    ddc.set_vels(lin, ang)
                    
                # Treat STOP, GRAB, and RELEASE identically for now: STOP THE WHEELS!
                elif cmd in ["STOP", "GRAB", "RELEASE"]:
                    ddc.set_vels(0.0, 0.0)
                    
            except ValueError:
                # If serial noise corrupts the numbers, ignore the bad message and keep going
                pass

    # 2. 100Hz Telemetry Feedback to Pi
    toc = ticks_us()
    if toc - tic >= 10_000:  
        meas_lin_vel, meas_ang_vel = ddc.get_vels()
        out_msg = f"{meas_lin_vel}, {meas_ang_vel}\n"
        sys.stdout.write(out_msg)
        tic = ticks_us()
        ol.toggle()