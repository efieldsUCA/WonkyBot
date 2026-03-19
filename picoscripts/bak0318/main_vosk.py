from machine import Pin, PWM
import sys

# --- LED ---
# "WL_GPIO0" is used for Pico W onboard LED on some firmwares, 
# but "LED" works on modern MicroPython.
led = Pin("LED", Pin.OUT)

# --- LEFT MOTOR ---
# Pulled from main.py left_ids = (3, 2, 4)
ph_l = Pin(3, Pin.OUT)    # Phase (Direction)
en_l = PWM(Pin(2))        # Enable (PWM / Speed)
en_l.freq(1000)
slp_l = Pin(4, Pin.OUT)   # Sleep
slp_l.value(1)            # Wake up

# --- RIGHT MOTOR ---
# Pulled from main.py right_ids = (6, 7, 8)
ph_r = Pin(6, Pin.OUT)    # Phase (Direction)
en_r = PWM(Pin(7))        # Enable (PWM / Speed)
en_r.freq(1000)
slp_r = Pin(8, Pin.OUT)   # Sleep
slp_r.value(1)            # Wake up

def set_motors(l_speed, l_dir, r_speed, r_dir):
    ph_l.value(l_dir)
    ph_r.value(r_dir)
    en_l.duty_u16(int(l_speed * 65535))
    en_r.duty_u16(int(r_speed * 65535))

def stop():
    en_l.duty_u16(0)
    en_r.duty_u16(0)

while True:
    line = sys.stdin.readline().strip()
    if not line:
        continue

    led.toggle()

    if line == "F":
        set_motors(0.5, 1, 0.5, 1)

    elif line == "L":
        set_motors(0.4, 0, 0.4, 1)

    elif line == "R":
        set_motors(0.4, 1, 0.4, 0)

    elif line == "S":
        stop()

    elif line == "SCAN":
        set_motors(0.3, 1, 0.3, 0)

    else:
        stop()