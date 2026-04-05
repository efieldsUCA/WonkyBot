import rclpy
from rclpy.node import Node

from tf_transformations import euler_from_quaternion

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry

from math import sin, cos, atan2, hypot

KP_V = 0.5
KP_W = 1.0
MAX_V = 0.3
MAX_W = 0.5
DIST_TOLERANCE = 0.05


class BlindNavigator(Node):
    def __init__(self):
        super().__init__("blind_navigation")
        # Create velocity publisher
        self.targ_vel_pubr = self.create_publisher(
            msg_type=Twist,
            topic="/cmd_vel",
            qos_profile=1,
        )
        # Create subscriber
        self.odom_subr = self.create_subscription(
            Odometry,
            "/odometry/filtered",
            self.approach_goal,
            1,
        )

        # variables
        self.goal_x = 1.0
        self.goal_y = 0.3
        self.is_goal_reached = True
        # Log
        self.get_logger().info("---\nBlind Navigator is activated.\n---")

    def approach_goal(self, odom_msg):
        """
        Calculates the command velocities to reach the target coordinates.
        Returns: cmd_vel
        """
        dx = self.goal_x - odom_msg.pose.pose.position.x
        dy = self.goal_y - odom_msg.pose.pose.position.y
        distance_error = hypot(dx, dy)
        if distance_error < DIST_TOLERANCE:
            self.is_goal_reached = True
            self.targ_lin_vel = 0.0  # Stop the robot
            self.targ_ang_vel = 0.0  # Stop the robot
        else:
            self.is_goal_reached = False
            target_heading = atan2(dy, dx)
            quat = [
                odom_msg.pose.pose.orientation.x,
                odom_msg.pose.pose.orientation.y,
                odom_msg.pose.pose.orientation.z,
                odom_msg.pose.pose.orientation.w,
            ]
            _, _, theta = euler_from_quaternion(quat)
            heading_error = target_heading - theta
            heading_error = atan2(sin(heading_error), cos(heading_error))
            cmd_w = KP_W * heading_error
            direction_alignment = max(
                0.0, cos(heading_error)
            )  # slow down if heading too off
            cmd_v = KP_V * distance_error * direction_alignment

            cmd_vel_msg = Twist()
            cmd_vel_msg.linear.x = max(min(cmd_v, MAX_V), -MAX_V)
            cmd_vel_msg.angular.z = max(min(cmd_w, MAX_W), -MAX_W)
            self.targ_vel_pubr.publish(cmd_vel_msg)

    def set_goal(self, goal_x, goal_y):
        self.goal_x = goal_x
        self.goal_y = goal_y
        self.is_goal_reached = False


def main(args=None):
    rclpy.init(args=args)
    blind_navigator = BlindNavigator()
    rclpy.spin(blind_navigator)
    blind_navigator.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
