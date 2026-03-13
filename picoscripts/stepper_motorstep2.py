from machine import Pin, Timer


class StepperMotor:
    def __init__(self, dir_id, step_id, en_id, pulse_width=60) -> None:
        """
        Make sure block start at the middle
        """
        self.dir_pin = Pin(dir_id, Pin.OUT)
        self.step_pin = Pin(step_id, Pin.OUT)
        self.en_pin = Pin(en_id, Pin.OUT)
        self.step_timer = Timer(
            mode=Timer.PERIODIC,
            freq=1_000_000 // (pulse_width * 2),
            callback=self.pulsate,
        )
        # Variables
        self.pulse_counts = 0  # TODO: top/mid/bottom calibration
        # Init
        self.disable()

    def pulsate(self, timer):
        if self.dir_pin.value():  # lowering
            if self.pulse_counts >= -50_000:
                self.step_pin.toggle()
                self.pulse_counts -= 0.5
        else:
            if self.pulse_counts <= 200_000:
                self.step_pin.toggle()
                self.pulse_counts += 0.5

        # if -20_000 <= self.pulse_counts <= 20_000:
        #     self.step_pin.toggle()
        #     if self.step_pin.value():
        #         if self.dir_pin.value():
        #             self.pulse_counts += 1
        #         else:
        #             self.pulse_counts -= 1
        # else:  # over the limit
        #     self.step_pin.off()

    def set_dir(self, direction):
        assert direction in (-1, 0, 1)
        if direction == 1:  # lowering
            self.enable()
            self.dir_pin.value(0)
        elif direction == -1:
            self.enable()
            self.dir_pin.value(1)
        else:
            self.disable()

    def enable(self):
        self.en_pin.value(0)

    def disable(self):
        self.en_pin.value(1)


if __name__ == "__main__":
    from utime import sleep
    from machine import freq, lightsleep

    freq(240_000_000)

    s = StepperMotor(
        dir_id=27,
        step_id=26,
        en_id=22,
    )
    s.set_dir(1)
    sleep(10)
    print(s.pulse_counts)
    s.set_dir(-1)
    sleep(20)
    print(s.pulse_counts)
    s.set_dir(1)
    sleep(10)
    s.set_dir(0)
    sleep(1)
    # TERMINATE
    freq(150_000_000)
    # lightsleep()
    
if __name__ == "__main__":
    from utime import sleep
    from machine import freq, lightsleep

        a = StepperMotor(
        dir_id=27,
        step_id=26,
        en_id=22,
    )
    a.set_dir(1)
    sleep(10)
    print(s.pulse_counts)
    a.set_dir(-1)
    sleep(20)
    print(s.pulse_counts)
    a.set_dir(1)
    sleep(10)
    a.set_dir(0)
    sleep(1)
    # TERMINATE
    freq(150_000_000)
    # lightsleep()
