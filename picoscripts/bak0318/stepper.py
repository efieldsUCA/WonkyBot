from machine import Pin
import utime

class Stepper:
    def __init__(self, step_pin, dir_pin):
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.delay_us = 800  # timing handled by main thread

    def step(self, direction):
        self.dir_pin.value(direction)
        self.step_pin.value(1)
        utime.sleep_us(10)   # pulse width
        self.step_pin.value(0)