from wheel_driver import WheelDriver
from machine import Timer


class WheelController(WheelDriver):
    def __init__(self, driver_ids, encoder_ids) -> None:
        super().__init__(driver_ids, encoder_ids)
        # Variables
        self.target_vel = 0.0
        self.err = 0.0
        self.prev_err = 0.0
        self.sum_err = 0.0
        self.d_err = 0.0
        self.duty = 0
        self.reg_vel_counter = 0  # to restrict vel regulating time
        # Constants
        self.reg_vel_freq = 25
        self.K_P = 0.5
        self.K_I = 0.0
        self.K_D = 0.0
        # Init timer
        self.vel_regulator = Timer(
            mode=Timer.PERIODIC, freq=self.reg_vel_freq, callback=self.regulate_velocity
        )

    def regulate_velocity(self, timer):
        """
        Spin motor to approach target linear velocity for 1 second
        """
        # No need for PID control if target velocity is 0
        if self.target_vel == 0 or self.reg_vel_counter > self.reg_vel_freq:
            self.brake()
        else:
            self.err = self.target_vel - self.lin_vel
            self.sum_err += self.err  # err_sum = err_sum + err
            self.diff_err = self.err - self.prev_err
            self.prev_err = self.err  # don't forget updating previous error
            inc_duty = (
                self.K_P * self.err + self.K_I * self.sum_err + self.K_D * self.diff_err
            )
            self.duty += inc_duty
            if self.duty > 0:  # forward
                if self.duty > 1:
                    self.duty = 1
                self.forward(self.duty)
            elif self.duty < 0:  # backward
                if self.duty < -1:
                    self.duty = -1
                self.backward(-self.duty)  # self.duty is negative
            else:
                self.stop()
            self.reg_vel_counter += 1

    def set_lin_vel(self, target_vel):
        """
        Set a reference LINEAR VELOCITY for this wheel
        """
        if target_vel is not self.target_vel:
            self.target_vel = target_vel
            self.sum_err = 0.0
            self.reg_vel_counter = 0


# TEST
if __name__ == "__main__":
    from time import sleep

    # wc = WheelController((3, 2, 4), (21, 20))
    wc = WheelController((6, 7, 8), (11, 10))
    print(f"target velocity: {wc.target_vel}")
    for v in range(1, 11):
        wc.set_lin_vel(v / 10)
        sleep(1)
        print(f"target velocity: {wc.target_vel}, actual velocity: {wc.lin_vel}")
    for v in reversed(range(10)):
        wc.set_lin_vel(v / 10)
        sleep(1)
        print(f"target velocity: {wc.target_vel}, actual velocity: {wc.lin_vel}")
    for v in range(1, 11):
        wc.set_lin_vel(-v / 10)
        sleep(1)
        print(f"target velocity: {wc.target_vel}, actual velocity: {wc.lin_vel}")
    for v in reversed(range(10)):
        wc.set_lin_vel(-v / 10)
        sleep(1)
        print(f"target velocity: {wc.target_vel}, actual velocity: {wc.lin_vel}")
    wc.set_lin_vel(0)
    sleep(1)