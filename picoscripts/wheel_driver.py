from motor_driver import MotorDriver
from machine import Pin, Timer
from math import pi


class WheelDriver(MotorDriver):
    def __init__(self, driver_ids, encoder_ids) -> None:
        super().__init__(*driver_ids)
        self.enc_a_pin = Pin(encoder_ids[0], Pin.IN)
        self.enc_b_pin = Pin(encoder_ids[1], Pin.IN)
        self.enc_a_pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update_counts_a
        )
        self.enc_b_pin.irq(
            trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self._update_counts_b
        )
        # variables
        self._enc_a_val = self.enc_a_pin.value()
        self._enc_b_val = self.enc_b_pin.value()
        self.prev_counts = 0
        self.ang_vel = 0.0
        self.lin_vel = 0.0

        # Constants
        self.WHEEL_RADIUS = 0.080  # meters (~6.3 inch diameter tire)
        self.CPR = 64
        self.GEAR_RATIO = 70
        self.vel_probe_freq = 50  # Hz

        # Init timer for velocity probing
        self.vel_probe = Timer(
            mode=Timer.PERIODIC, freq=self.vel_probe_freq, callback=self.probe_velocity
        )
        # Init counts
        self.reset_encoder_counts()

    def _update_counts_a(self, pin):
        self._enc_a_val = pin.value()
        if self._enc_a_val == 1:
            if self._enc_b_val == 0:  # a=1, b=0
                self.encoder_counts += 1
            else:  # a=1, b=1
                self.encoder_counts -= 1
        else:
            if self._enc_b_val == 0:  # a=0, b=0
                self.encoder_counts -= 1
            else:  # a=0, b=1
                self.encoder_counts += 1

    def _update_counts_b(self, pin):
        self._enc_b_val = pin.value()
        if self._enc_b_val == 1:
            if self._enc_a_val == 0:  # b=1, a=0
                self.encoder_counts -= 1
            else:  # b=1, a=1
                self.encoder_counts += 1
        else:
            if self._enc_a_val == 0:  # b=0, a=0
                self.encoder_counts += 1
            else:  # b=0, a=1
                self.encoder_counts -= 1

    def probe_velocity(self, timer):
        curr_counts = self.encoder_counts
        d_counts = curr_counts - self.prev_counts
        self.prev_counts = curr_counts  # update previous encoder counts
        d_rad = d_counts / (self.CPR * self.GEAR_RATIO) * 2 * pi  # radians
        self.ang_vel = d_rad / (1 / self.vel_probe_freq)  # rad/s
        self.lin_vel = self.WHEEL_RADIUS * self.ang_vel  # m/s
        return self.ang_vel, self.lin_vel

    def reset_encoder_counts(self):
        self.encoder_counts = 0


# TEST
if __name__ == "__main__":  # Test only the encoder part
    from time import sleep

    # SETUP
    # wd = WheelDriver((3, 2, 4), (21, 20))
    wd = WheelDriver((6, 7, 8), (11, 10))
    curr_counts = 0
    prev_counts = 0
    dt = 0.04

    # LOOP
    # Forwardly ramp up and down
    for i in range(100):
        wd.forward((i + 1) / 100)
        sleep(dt)  # 4 seconds to ramp up
        print(f"angular velocity: {wd.ang_vel}, linear velocity: {wd.lin_vel}")
    for i in reversed(range(100)):
        wd.forward((i + 1) / 100)
        sleep(dt)  # 4 seconds to ramp down
        print(f"angular velocity: {wd.ang_vel}, linear velocity: {wd.lin_vel}")
    # Backwardly ramp up and down
    for i in range(100):
        wd.backward((i + 1) / 100)
        sleep(dt)  # 4 seconds to ramp up
        print(f"angular velocity: {wd.ang_vel}, linear velocity: {wd.lin_vel}")
    for i in reversed(range(100)):
        wd.backward((i + 1) / 100)
        sleep(dt)  # 4 seconds to ramp down
        print(f"angular velocity: {wd.ang_vel}, linear velocity: {wd.lin_vel}")

    # Terminate
    wd.halt()
    print("Motor driver disabled!")