from machine import Pin, PWM


class MotorDriver:
    def __init__(self, ina_id, inb_id, pwm_id):
        self.ina_pin = Pin(ina_id, Pin.OUT)
        self.inb_pin = Pin(inb_id, Pin.OUT)
        self.pwm_pin = PWM(Pin(pwm_id))
        self.pwm_pin.freq(1000)
        # Stop motor
        self.stop()
        self.halt()

    def halt(self):
        self.ina_pin.off()
        self.inb_pin.off()

    def stop(self):
        self.pwm_pin.duty_u16(0)

    def brake(self):
        """Active brake: shorts motor terminals to stop quickly instead of coasting."""
        self.ina_pin.on()
        self.inb_pin.on()
        self.pwm_pin.duty_u16(65535)

    def forward(self, duty: float = 0.0):
        assert 0 <= duty <= 1  # make sure speed in range [0, 1]
        self.ina_pin.off()
        self.inb_pin.on()
        self.pwm_pin.duty_u16(int(65535 * duty))

    def backward(self, duty: float = 0.0):
        assert 0 <= duty <= 1  # make sure speed in range [0, 1]
        self.ina_pin.on()
        self.inb_pin.off()
        self.pwm_pin.duty_u16(int(65535 * duty))


if __name__ == "__main__":
    from time import sleep

    # SETUP
    #md = MotorDriver(3, 2, 4)
    md = MotorDriver(6, 7, 8)

    # LOOP
    for i in range(100):
        md.forward((i + 1) / 100)
        print(f"f, dc: {i}%")
        sleep(4 / 100)  # 4 seconds to ramp up
    for i in reversed(range(100)):
        md.forward((i + 1) / 100)
        print(f"f, dc: {i}%")
        sleep(4 / 100)  # 4 seconds to ramp down
    # Backwardly ramp up and down
    for i in range(100):
        md.backward((i + 1) / 100)
        print(f"b, dc: {i}%")
        sleep(4 / 100)  # 4 seconds to ramp up
    for i in reversed(range(100)):
        md.backward((i + 1) / 100)
        print(f"b, dc: {i}%")
        sleep(4 / 100)  # 4 seconds to ramp down

    # TERMINATE
    md.stop()
    print("motor stopped.")
    sleep(0.1)  # full stop
    md.halt()
    print("motor driver disabled.")