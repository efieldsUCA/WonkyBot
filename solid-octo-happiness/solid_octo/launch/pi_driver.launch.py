"""
pi_driver.launch.py
Runs on the Raspberry Pi ONLY. Starts all hardware drivers:
  - Motor controller (octo_pilot)
  - RPLidar
  - RealSense camera (with aligned depth)
  - Joystick teleop
  - TF publishers (base_footprint, lidar_link, camera_link)

Everything else (Nav2, mapping, detection, sorting) runs on the laptop.

Usage:
  ros2 launch solid_octo pi_driver.launch.py
"""

import os
from math import pi
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
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

    # RPLidar
    rplidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(control_package_path / "launch/rplidar.launch.py")
        ),
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

    # TF: base_link -> lidar_link
    lidar_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="lidar_tf",
        arguments=[
            "--x", "0.15", "--y", "0", "--z", "0.2",
            "--yaw", str(pi), "--pitch", "0", "--roll", "0",
            "--frame-id", "base_link",
            "--child-frame-id", "lidar_link",
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
        rplidar_launch,
        realsense_launch,
        teleop_launch,
        footprint_tf,
        lidar_tf,
        camera_tf,
    ])
