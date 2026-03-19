from wheel_controller import WheelController


class DiffDriveController:
    def __init__(self, left_ids, right_ids) -> None:
        self.left_wheel = WheelController(*left_ids)
        self.right_wheel = WheelController(*right_ids)

        # Variables
        self.meas_lin_vel = 0.0
        self.meas_ang_vel = 0.0

        # Constants
        self.WHEEL_SEP = 0.406  # wheel separation in meters (~16 inches)

    def get_vels(self):
        """
        Get actual velocities
        """
        self.meas_lin_vel = 0.5 * (
            self.left_wheel.lin_vel + self.right_wheel.lin_vel
        )  # robot's linear velocity
        self.meas_ang_vel = (
            self.right_wheel.lin_vel - self.left_wheel.lin_vel
        ) / self.WHEEL_SEP  # robot's angular velocity
        return self.meas_lin_vel, self.meas_ang_vel

    def set_vels(self, target_lin_vel, target_ang_vel):
        """
        Set reference velocities
        """
        left_targ_lin_vel = target_lin_vel - 0.5 * (target_ang_vel * self.WHEEL_SEP)
        right_targ_lin_vel = target_lin_vel + 0.5 * (target_ang_vel * self.WHEEL_SEP)
        self.left_wheel.set_lin_vel(left_targ_lin_vel)
        self.right_wheel.set_lin_vel(right_targ_lin_vel)


if __name__ == "__main__":
    from time import sleep
    from math import pi, sin

    ddc = DiffDriveController(
        left_ids=((3, 2, 4), (21, 20)), right_ids=((6, 7, 8), (11, 10))
    )
    phases = [-pi, -3 * pi / 4, -pi / 2, -pi / 4, 0, pi / 4, pi / 2, 3 * pi / 4, pi]
    for av in phases:
        for lv in phases:
            targ_ang_vel = av
            targ_lin_vel = sin(lv)
            ddc.set_vels(targ_lin_vel, targ_ang_vel)
            sleep(1)
            meas_lin_vel, meas_ang_vel = ddc.get_vels()
            print(
                f"target vel: {targ_lin_vel} m/s, {targ_ang_vel} rad/s\nactual vel: {meas_lin_vel} m/s, {meas_ang_vel} rad/s\n"
            )
    ddc.set_vels(0.0, 0.0)