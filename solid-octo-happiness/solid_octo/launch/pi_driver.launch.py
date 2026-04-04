"""
pi_driver.launch.py
Runs on the Raspberry Pi ONLY. Starts all hardware drivers:
  - Motor controller (octo_pilot)
  - RealSense camera (with aligned depth)
  - Depth-to-laserscan (converts depth image to /scan)
  - Joystick teleop
  - TF publishers (base_footprint, camera_link)

Everything else (Nav2, mapping, detection, sorting) runs on the laptop.

Usage (on Pi, or via SSH from laptop):
  ros2 launch solid_octo pi_driver.launch.py
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory, get_package_share_path


def generate_launch_description():
    control_package_path = get_package_share_path("solid_octo")
    joy_config_path = control_package_path / "configs/xbox.config.yaml"

    # Motor controller
    octo_pilot_node = Node(
        package="solid_octo",
        executable="octo_pilot",
        output="screen",
    )

    # RealSense camera with aligned depth
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("realsense2_camera"),
                         "launch", "rs_launch.py")
        ]),
        launch_arguments={
            "align_depth.enable": "true",
        }.items(),
    )

    # Depth image -> 2D laser scan (used by RTABMAP and Nav2 for /scan)
    depth_to_laser = Node(
        package="depthimage_to_laserscan",
        executable="depthimage_to_laserscan_node",
        name="depthimage_to_laserscan",
        output="screen",
        remappings=[
            ("depth", "/camera/camera/depth/image_rect_raw"),
            ("depth_camera_info", "/camera/camera/depth/camera_info"),
            ("scan", "/scan"),
        ],
        parameters=[{
            "output_frame": "camera_link",
            "range_min": 0.35,
            "range_max": 4.0,
            "scan_height": 10,
        }],
    )

    # Joystick teleop
    teleop_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(get_package_share_path("teleop_twist_joy") / "launch/teleop-launch.py")
        ),
        launch_arguments={"config_filepath": str(joy_config_path)}.items(),
    )

    # TF: base_link -> base_footprint
    footprint_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_footprint_tf",
        arguments=[
            "--x", "0", "--y", "0", "--z", "-0.05",
            "--yaw", "0", "--pitch", "0", "--roll", "0",
            "--frame-id", "base_link",
            "--child-frame-id", "base_footprint",
        ],
    )

    # TF: base_link -> camera_link
    camera_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="camera_tf",
        arguments=[
            "--x", "0.43", "--y", "0", "--z", "0.10",
            "--yaw", "0", "--pitch", "0", "--roll", "0",
            "--frame-id", "base_link",
            "--child-frame-id", "camera_link",
        ],
    )

    return LaunchDescription([
        octo_pilot_node,
        realsense_launch,
        # Delay laserscan until camera is up
        TimerAction(period=3.0, actions=[depth_to_laser]),
        teleop_launch,
        footprint_tf,
        camera_tf,
    ])
