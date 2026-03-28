import rclpy
from rclpy.node import Node

from tf_transformations import quaternion_about_axis

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry

import serial
from math import sin, cos, atan2


class OctoPilot(Node):
    def __init__(self):
        super().__init__("octo_pilot")
        # Create serial communication to Pico
        self.pico_msngr = serial.Serial("/dev/ttyACM0", 115200, timeout=0.01)
        self.pico_comm_timer = self.create_timer(0.0133, self.process_pico_message)
        # Create target velocity subscriber
        self.targ_vel_subr = self.create_subscription(
            topic="/cmd_vel",
            msg_type=Twist,
            callback=self.set_targ_vels,
            qos_profile=1,
        )
        # Create odometry publisher
        self.odom_pubr = self.create_publisher(
            topic="/odom",
            msg_type=Odometry,
            qos_profile=1,
        )
        # variables
        self.motion_data = {key: 0.0 for key in ["meas_lin_vel", "meas_ang_vel"]}
        self.targ_lin_vel = 0.0
        self.targ_ang_vel = 0.0
        self.pose = {key: 0.0 for key in ["x", "y", "theta"]}
        self.prev_ts = self.get_clock().now()
        self.curr_ts = self.get_clock().now()
        self.set_vel_ts = self.get_clock().now()
        # Constants
        self.GROUND_CLEARANCE = 0.0375
        # Log
        self.get_logger().info("---\nOcto driver is up.\n---")

    def set_targ_vels(self, msg):
        self.set_vel_ts = self.get_clock().now()
        self.targ_lin_vel = msg.linear.x
        self.targ_ang_vel = msg.angular.z
        self.get_logger().debug(
            f"Set target velocity\nlinear: {self.targ_lin_vel}, angular: {self.targ_ang_vel}"
        )

    def process_pico_message(self):
        # Transmit velocity commands to Pico
        msg_to_pico = f"{self.targ_lin_vel:.3f},{self.targ_ang_vel:.3f}\n"
        self.pico_msngr.write(msg_to_pico.encode("utf-8"))
        self.get_logger().debug(f"target vels:\n---\n{msg_to_pico}")  # debug
        # Receive motion data from Pico
        if self.pico_msngr.inWaiting() > 0:
            msg_from_pico = self.pico_msngr.readline().decode("utf-8", "ignore").strip()
            if msg_from_pico:
                data_strings = msg_from_pico.split(",")
                if len(data_strings) == 2:
                    try:
                        self.motion_data.update(
                            zip(
                                self.motion_data.keys(),
                                map(
                                    float, data_strings
                                ),  # convert all str in list to float
                            )
                        )
                    except ValueError:
                        pass
        self.get_logger().debug(f"Motion data:\n---\n{self.motion_data}")  # debug
        self.curr_ts = self.get_clock().now()
        # Update pose
        dt = (self.curr_ts - self.prev_ts).nanoseconds * 1e-9
        dx = self.motion_data["meas_lin_vel"] * cos(self.pose["theta"]) * dt
        dy = self.motion_data["meas_lin_vel"] * sin(self.pose["theta"]) * dt
        dth = self.motion_data["meas_ang_vel"] * dt
        self.pose["x"] += dx
        self.pose["y"] += dy
        self.pose["theta"] += dth
        self.pose["theta"] = atan2(
            sin(self.pose["theta"]), cos(self.pose["theta"])
        )  # restrict value: [-pi, pi]
        quat = quaternion_about_axis(self.pose["theta"], (0, 0, 1))
        self.prev_ts = self.curr_ts  # update time stamp
        # Publish odom topic
        odom_msg = Odometry()
        odom_msg.header.stamp = self.curr_ts.to_msg()
        odom_msg.header.frame_id = "odom"
        odom_msg.child_frame_id = "base_link"
        odom_msg.pose.pose.position.x = self.pose["x"]
        odom_msg.pose.pose.position.y = self.pose["y"]
        odom_msg.pose.pose.position.z = self.GROUND_CLEARANCE
        odom_msg.pose.pose.orientation.x = quat[0]
        odom_msg.pose.pose.orientation.y = quat[1]
        odom_msg.pose.pose.orientation.z = quat[2]
        odom_msg.pose.pose.orientation.w = quat[3]
        odom_msg.twist.twist.linear.x = self.motion_data["meas_lin_vel"]
        odom_msg.twist.twist.angular.z = self.motion_data["meas_ang_vel"]
        self.odom_pubr.publish(odom_msg)
        # Clear target velocity after 0.5 s idling
        if (self.curr_ts - self.set_vel_ts).nanoseconds > 500_000_000:
            self.targ_lin_vel = 0.0
            self.targ_ang_vel = 0.0


def main(args=None):
    rclpy.init(args=args)
    octo_pilot = OctoPilot()
    rclpy.spin(octo_pilot)
    octo_pilot.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
