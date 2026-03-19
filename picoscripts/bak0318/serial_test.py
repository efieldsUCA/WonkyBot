# Fast stepper test for Raspberry Pi Pico - MODIFIED FOR TWO MOTORS
# Motor 1: DIR = GP27, STEP = GP26
# Motor 2: DIR = GP13, STEP = GP12
#
# CONTROL:
# W = Motor 1, Direction 0
# S = Motor 1, Direction 1
# A = Motor 2, Direction 0
# D = Motor 2, Direction 1

from machine import Pin
import utime
import sys
import uselect  # For non-blocking keyboard input

# === CONFIG ===
# --- Motor 1 Pins ---
DIR1_PIN = 27
STEP1_PIN = 26

# --- Motor 2 Pins ---
DIR2_PIN = 13
STEP2_PIN = 12

# --- Shared Movement Settings ---
STEPS = 60000     # Total steps for the move
MIN_DELAY_US = 1000 # Slowest delay (start/end speed)
MAX_SPEED_US = 50   # Fastest delay (target speed)
ACCEL_STEPS = 1000  # Steps used to ramp up and ramp down

# === Setup Pins ===
# Motor 1
dir1_pin = Pin(DIR1_PIN, Pin.OUT)
step1_pin = Pin(STEP1_PIN, Pin.OUT, value=0)

# Motor 2
dir2_pin = Pin(DIR2_PIN, Pin.OUT)
step2_pin = Pin(STEP2_PIN, Pin.OUT, value=0)


def single_pulse(step_pin_obj, delay_us):
    """Sends a single step pulse to the specified step pin."""
    step_pin_obj.value(1)
    # This 14us pulse width is from your original code.
    # It might need to be adjusted for your specific driver.
    utime.sleep_us(14)
    step_pin_obj.value(0)
    utime.sleep_us(delay_us)

def move_steps(step_pin_obj, dir_pin_obj, n_steps, direction):
    """Moves a specific motor a number of steps with acceleration."""
   
    # Set the direction
    dir_pin_obj.value(direction)
    utime.sleep_ms(10) # Short delay after setting direction

    # Adjust ramp if n_steps is too small for the full acceleration
    if n_steps < 2 * ACCEL_STEPS:
        steps_for_ramp = n_steps // 2
    else:
        steps_for_ramp = ACCEL_STEPS

    # Acceleration ramp
    for i in range(steps_for_ramp):
        d = int(MIN_DELAY_US - (MIN_DELAY_US - MAX_SPEED_US) * i / steps_for_ramp)
        single_pulse(step_pin_obj, d)

    # Constant speed section
    constant_steps = n_steps - 2 * steps_for_ramp
    for i in range(constant_steps):
        single_pulse(step_pin_obj, MAX_SPEED_US)

    # Deceleration ramp
    for i in range(steps_for_ramp, 0, -1):
        d = int(MIN_DELAY_US - (MIN_DELAY_US - MAX_SPEED_US) * i / steps_for_ramp)
        single_pulse(step_pin_obj, d)

# === MAIN EXECUTION ===
# This new main loop waits for keyboard commands

print("--- Stepper Motor Control ---")
print("Press key in terminal to move:")
print("  W: Motor 1, Dir 0")
print("  S: Motor 1, Dir 1")
print("  A: Motor 2, Dir 0")
print("  D: Motor 2, Dir 1")
print("-----------------------------")

# Set up the poller to read from STDIN (USB serial)
poller = uselect.poll()
poller.register(sys.stdin, uselect.POLLIN)

while True:
    # Check if there is a character waiting in the input buffer
    if poller.poll(0):
        char = sys.stdin.read(1) # Read one character
       
        if char == 'w':
            print("Running W: Motor 1, Dir 0...")
            move_steps(step1_pin, dir1_pin, STEPS, 0)
            utime.sleep_ms(3000)
            print("Ready.")

        elif char == 's':
            print("Running S: Motor 1, Dir 1...")
            move_steps(step1_pin, dir1_pin, STEPS, 1)
            utime.sleep_ms(1000)
            print("Ready.")
           
        elif char == 'a':
            print("Running A: Motor 2, Dir 0...")
            move_steps(step2_pin, dir2_pin, STEPS, 0)
            # No extra sleep specified for 'a'
            print("Ready.")

        elif char == 'd':
            print("Running D: Motor 2, Dir 1...")
            move_steps(step2_pin, dir2_pin, STEPS, 1)
            utime.sleep_ms(1000)
            print("Ready.")

    # Small delay to keep the loop from running too fast
    utime.sleep_ms(10)