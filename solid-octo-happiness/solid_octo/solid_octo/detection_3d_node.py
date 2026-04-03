#!/usr/bin/env python3
"""
detection_3d_node.py
Subscribes to /detected_objects (from detector_node) and the depth image.
Deprojects each detection's (cx, cy) pixel to a 3D point in camera frame,
then transforms to odom frame using the robot's pose.
Publishes enriched detections on /detected_objects_3d.
"""

import json
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
from nav_msgs.msg import Odometry


def transform_cam_to_odom(coords_cam, robot_pose):
    coords_cam_arr = np.array(coords_cam)
    X, Y, theta = robot_pose

    # Static transform: camera_link to base_link
    R_c_b = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]])
    t_c_b = np.array([-0.64, 0.0, 0.2])

    coords_base = R_c_b @ coords_cam_arr + t_c_b

    # Dynamic transform: base_link to odom
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    R_b_o = np.array([[cos_t, -sin_t, 0.0], [sin_t, cos_t, 0.0], [0.0, 0.0, 1.0]])
    t_b_o = np.array([X, Y, 0.0])

    coords_odom = R_b_o @ coords_base + t_b_o
    return coords_odom


def yaw_from_quaternion(q):
    """Extract yaw from geometry_msgs Quaternion."""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def deproject_pixel(cx, cy, depth_m, intrinsics):
    """Deproject a 2D pixel + depth to 3D point using camera intrinsics."""
    fx, fy = intrinsics["fx"], intrinsics["fy"]
    ppx, ppy = intrinsics["ppx"], intrinsics["ppy"]
    x = (cx - ppx) / fx * depth_m
    y = (cy - ppy) / fy * depth_m
    z = depth_m
    return (x, y, z)


class Detection3DNode(Node):

    def __init__(self):
        super().__init__("detection_3d_node")

        self.bridge = CvBridge()
        self.depth_frame = None
        self.intrinsics = None
        self.robot_pose = (0.0, 0.0, 0.0)  # (X, Y, theta)
        self.latest_detections = []

        # Publishers
        self.pub_3d = self.create_publisher(String, "/detected_objects_3d", 10)

        # Subscribers
        self.create_subscription(
            String, "/detected_objects",
            self.detections_cb, 10)
        self.create_subscription(
            Image, "/camera/camera/aligned_depth_to_color/image_raw",
            self.depth_cb, qos_profile_sensor_data)
        self.create_subscription(
            CameraInfo, "/camera/camera/color/camera_info",
            self.camera_info_cb, qos_profile_sensor_data)
        self.create_subscription(
            Odometry, "/odom",
            self.odom_cb, 10)

        self.get_logger().info("detection_3d_node ready")

    def depth_cb(self, msg: Image):
        try:
            self.depth_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception:
            pass

    def camera_info_cb(self, msg: CameraInfo):
        if self.intrinsics is None:
            self.intrinsics = {
                "fx": msg.k[0],
                "fy": msg.k[4],
                "ppx": msg.k[2],
                "ppy": msg.k[5],
            }
            self.get_logger().info(
                f"Got intrinsics: fx={self.intrinsics['fx']:.1f} fy={self.intrinsics['fy']:.1f} "
                f"ppx={self.intrinsics['ppx']:.1f} ppy={self.intrinsics['ppy']:.1f}"
            )

    def odom_cb(self, msg: Odometry):
        pos = msg.pose.pose.position
        yaw = yaw_from_quaternion(msg.pose.pose.orientation)
        self.robot_pose = (pos.x, pos.y, yaw)

    def detections_cb(self, msg: String):
        try:
            detections = json.loads(msg.data)
        except json.JSONDecodeError:
            return

        if not detections or self.depth_frame is None or self.intrinsics is None:
            return

        # detector_node works at FRAME_W x FRAME_H, but depth is full resolution
        # Scale pixel coords from detector frame to full depth frame
        depth_h, depth_w = self.depth_frame.shape[:2]

        enriched = []
        for det in detections:
            # detector_node uses 480x360 frame, scale cx/cy to depth resolution
            scale_x = depth_w / 480.0
            scale_y = depth_h / 360.0
            cx_full = int(det["cx"] * scale_x)
            cy_full = int(det["cy"] * scale_y)

            # Sample depth: median of 9x9 patch around detection center
            r = 6
            patch = self.depth_frame[
                max(cy_full - r, 0):cy_full + r + 1,
                max(cx_full - r, 0):cx_full + r + 1
            ]
            valid = patch[patch > 0].astype(float)
            if len(valid) == 0:
                continue
            depth_m = float(np.median(valid)) / 1000.0

            if depth_m > 2.0 or depth_m < 0.1:
                continue

            # Deproject to 3D camera frame
            coords_cam = deproject_pixel(cx_full, cy_full, depth_m, self.intrinsics)

            # Transform to odom frame
            coords_odom = transform_cam_to_odom(coords_cam, self.robot_pose)

            det_3d = {
                "color": det["color"],
                "type": det["type"],
                "depth_m": round(depth_m, 3),
                "cam_xyz": [round(c, 3) for c in coords_cam],
                "odom_xyz": [round(c, 3) for c in coords_odom],
            }
            enriched.append(det_3d)

        if enriched:
            out = String()
            out.data = json.dumps(enriched)
            self.pub_3d.publish(out)
            summary = [(d["color"], d["type"], f"odom=({d['odom_xyz'][0]:.2f},{d['odom_xyz'][1]:.2f})") for d in enriched]
            self.get_logger().info(str(summary), throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = Detection3DNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
