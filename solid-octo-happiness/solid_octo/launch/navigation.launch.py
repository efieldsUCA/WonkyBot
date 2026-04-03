"""
navigation.launch.py
Runs on the LAPTOP over the same ROS2 network as the Pi.
Starts Nav2, depth-to-laserscan, detector, sorting_master, detection_3d,
and waypoint_navigator for autonomous ball sorting.

Prerequisites:
  - Pi is running: ros2 launch solid_octo pi_driver.launch.py
  - A saved map exists (from mapping.launch.py)
  - Same ROS_DOMAIN_ID and RMW_IMPLEMENTATION on both machines

Usage:
  ros2 launch solid_octo navigation.launch.py map:=/path/to/room_map.yaml

Arguments:
  map         - path to the map YAML file (required)
  params_file - path to nav2_params.yaml (optional, has default)
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    map_arg = DeclareLaunchArgument(
        "map",
        description="Full path to the map YAML file",
    )

    default_params = os.path.join(
        get_package_share_directory("nav2_bringup"), "params", "nav2_params.yaml"
    )
    params_arg = DeclareLaunchArgument(
        "params_file",
        default_value=default_params,
        description="Full path to nav2_params.yaml",
    )

    # Depth image -> fake 2D laser scan
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

    # Nav2 bringup (map server, AMCL, planner, controller, etc.)
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory("nav2_bringup"),
                         "launch", "bringup_launch.py")
        ]),
        launch_arguments={
            "map": LaunchConfiguration("map"),
            "params_file": LaunchConfiguration("params_file"),
            "use_sim_time": "False",
            "autostart": "True",
        }.items(),
    )

    # Detector node (color + depth detection)
    detector_node = Node(
        package="solid_octo",
        executable="detector_node",
        output="screen",
    )

    # 3D detection node (deprojects detections to odom frame)
    detection_3d_node = Node(
        package="solid_octo",
        executable="detection_3d",
        output="screen",
    )

    # Sorting master (vision-based fine approach + grab/release)
    sorting_master_node = Node(
        package="solid_octo",
        executable="sorting_master",
        output="screen",
    )

    # Waypoint navigator (sequencer: ball -> grab -> bucket -> release)
    waypoint_navigator_node = Node(
        package="solid_octo",
        executable="waypoint_navigator",
        output="screen",
    )

    return LaunchDescription([
        map_arg,
        params_arg,
        depth_to_laser,
        nav2_launch,
        # Delay detection and navigation nodes to let Nav2 start up
        TimerAction(period=5.0, actions=[detector_node]),
        TimerAction(period=5.0, actions=[detection_3d_node]),
        TimerAction(period=5.0, actions=[sorting_master_node]),
        TimerAction(period=30.0, actions=[waypoint_navigator_node]),
    ])
