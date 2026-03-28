from math import pi

from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    octo_package_path = get_package_share_path("solid_octo")
    joy_config_path = octo_package_path / "config/joy.yaml"
    ekf_config_path = octo_package_path / "config/ekf.yaml"

    sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="false",
        choices=["true", "false"],
        description="Flag to enable use simulation time",
    )

    footprint_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0",
            "--y",
            "0",
            "--z",
            "-0.0375",
            "--yaw",
            "0",
            "--pitch",
            "0",
            "--roll",
            "0",
            "--frame-id",
            "base_link",
            "--child-frame-id",
            "base_footprint",
        ],
    )

    camer_link_static_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        arguments=[
            "--x",
            "0.2",
            "--y",
            "0",
            "--z",
            "0",
            "--yaw",
            f"{-pi / 2}",
            "--pitch",
            "0",
            "--roll",
            f"{-pi / 2}",
            "--frame-id",
            "base_link",
            "--child-frame-id",
            "camera_link",
        ],
    )

    octo_pilot_node = Node(package="solid_octo", executable="octo_pilot")

    launch_realsense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(get_package_share_path("realsense2_camera") / "launch/rs_launch.py")
        ),
        launch_arguments={
            "align_depth.enable": "true",
            "unite_imu_method": "2",
            "enable_gyro": "true",
            "enable_accel": "true",
            "init_reset": "true",
        }.items(),
    )

    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[
            str(ekf_config_path),
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    )

    depthimage_to_laserscan_node = Node(
        package="depthimage_to_laserscan",
        executable="depthimage_to_laserscan_node",
        name="depthimage_to_laserscan_node",
        # output="screen",
        remappings=[
            ("/depth_camera_info", "/camera/camera/aligned_depth_to_color/camera_info"),
            ("/depth", "/camera/camera/aligned_depth_to_color/image_raw"),
        ],
        parameters=[
            {
                "output_frame": "camera_depth_frame",  # <--- The critical fix
                "scan_height": 5,  # Number of pixel rows to average
                "range_min": 0.5,  # Min distance (RealSense depends on model, usually 0.2m)
                "range_max": 12.0,  # Max distance
            }
        ],
    )

    launch_teleop_twist_joy = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(get_package_share_path("teleop_twist_joy") / "launch/teleop-launch.py")
        ),
        launch_arguments={
            "config_filepath": str(joy_config_path),
        }.items(),
    )

    return LaunchDescription(
        [
            sim_time_arg,
            footprint_static_tf,
            camer_link_static_tf,
            octo_pilot_node,
            launch_realsense,
            robot_localization_node,
            depthimage_to_laserscan_node,
            launch_teleop_twist_joy,
        ]
    )
