import cv2
import numpy as np
import threading
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

# 1. Target Library (Copy your HSV values here)
colors = {
    "red":    {"lower": [0, 150, 70],    "upper": [10, 255, 255], "draw": (0, 0, 255)},
    "green":  {"lower": [35, 60, 50],    "upper": [85, 255, 255], "draw": (0, 255, 0)},
    "blue":   {"lower": [100, 150, 50],  "upper": [140, 255, 255], "draw": (255, 0, 0)},
    "yellow": {"lower": [20, 100, 100],  "upper": [35, 255, 255], "draw": (0, 255, 255)},
}


class VisionTester(Node):
    def __init__(self):
        super().__init__("vision_tester")
        self.bridge = CvBridge()
        self.frame = None
        self.lock = threading.Lock()
        self.create_subscription(
            Image,
            "/camera/camera/color/image_raw",
            self.cb,
            qos_profile_sensor_data,
        )
        self.detection_publisher = self.create_publisher(
            Image,
            '/detection',
            1,
        )

        self.get_logger().info("Vision Tester started. Press 'q' in the window to quit.")

    def cb(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            if frame is None:
                return
            frame = cv2.resize(frame, (640, 480))
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for name, ranges in colors.items():
                mask = cv2.inRange(hsv, np.array(ranges["lower"]), np.array(ranges["upper"]))
                mask = cv2.erode(mask, None, iterations=2)
                mask = cv2.dilate(mask, None, iterations=2)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for c in contours:
                    area = cv2.contourArea(c)
                    if area > 1000:
                        x, y, w, h = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), ranges["draw"], 2)
                        cv2.putText(frame, f"{name} {int(area)}", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, ranges["draw"], 2)
            ros_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.detection_publisher.publish(ros_img_msg)
            with self.lock:
                self.frame = frame
        except Exception as e:
            import traceback
            self.get_logger().error(f"{e}\n{traceback.format_exc()}")


def main(args=None):
    rclpy.init(args=args)
    node = VisionTester()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)
            if node.frame is not None:
                cv2.imshow("Vision Tester", node.frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
