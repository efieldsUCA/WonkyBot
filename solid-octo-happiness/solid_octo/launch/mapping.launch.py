"""
mapping.launch.py
Runs on the LAPTOP over the same ROS2 network as the Pi.
Starts RTABMAP SLAM for map building.

Prerequisites:
  - Pi is running: ros2 launch solid_octo pi_driver.launch.py
  - Same ROS_DOMAIN_ID on both machines

Usage:
  ros2 launch solid_octo mapping.launch.py

When done mapping, save the map in a separate terminal:
  ros2 run nav2_map_server map_saver_cli -f ~/room_map -t /rtabmap/map
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # RTABMAP SLAM
    rtabmap_node = Node(
        package="rtabmap_slam",
        executable="rtabmap",
        name="rtabmap",
        output="screen",
        parameters=[{
            "frame_id": "base_link",
            "subscribe_depth": True,
            "subscribe_scan": True,
            "approx_sync": True,
            "queue_size": 20,
            "Reg/Strategy": "1",
            "Grid/RayTracing": "true",
            "RGBD/NeighborLinkRefining": "true",
            "use_sim_time": False,
        }],
        remappings=[
            ("rgb/image", "/camera/camera/color/image_raw"),
            ("depth/image", "/camera/camera/depth/image_rect_raw"),
            ("rgb/camera_info", "/camera/camera/color/camera_info"),
            ("scan", "/scan"),
            ("odom", "/odom"),
        ],
        arguments=["--delete_db_on_start"],
    )

    return LaunchDescription([
        rtabmap_node,
    ])
