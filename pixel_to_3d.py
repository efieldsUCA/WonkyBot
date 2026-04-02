import pyrealsense2 as rs

# Configure and start pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

def transform_cam_to_odom(coords_cam, robot_pose):
    """
    Transforms a 3D point from the camera frame to the odom frame.

    Args:
        coords_cam (list or tuple): (x_c, y_c, z_c) representing the object in the camera frame.
        robot_pose (list or tuple): (X, Y, theta) representing the robot's current odometry.
    Returns:
        coords_odom (numpy.ndarray): [x_o, y_o, z_o] representing the object in the odom frame.
    """
    # 1. Parse inputs into numpy arrays
    coords_cam_arr = np.array(coords_cam)
    X, Y, theta = robot_pose

    # 2. Static Transformation: camera_link to base_link
    R_c_b = np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]])
    t_c_b = np.array(
        [-0.64, 0.0, 0.2],  # 0.64 is the gap between camera and ball
    )  # Set camera displacement from robot's base center

    # Calculate point in base_link
    # p_b = R_c_b @ coords_cam_arr + t_c_b
    coords_base_arr = R_c_b @ coords_cam_arr + t_c_b

    # 3. Dynamic Transformation: base_link to odom
    # Building the rotation matrix manually for speed (Z-axis rotation only)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    R_b_o = np.array([[cos_t, -sin_t, 0.0], [sin_t, cos_t, 0.0], [0.0, 0.0, 1.0]])
    t_b_o = np.array([X, Y, 0.0])  # Robot's position on the ground plane

    # Calculate final point in odom
    coords_odom = R_b_o @ coords_base_arr + t_b_o

    return coords_odom

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # Define pixel coordinates (x, y)
        x, y = 320, 240  # Example: center of image

        # Get depth (Z) in meters
        depth_in_meters = depth_frame.get_distance(x, y)

        # Get intrinsics of depth stream
        intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics

        # Convert 2D pixel to 3D point (X, Y, Z in meters)
        coords_cam = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], depth_in_meters)

        print(f"3D Coordinates (X, Y, Z): {coords_cam[0]:.3f}, {coords_cam[1]:.3f}, {coords_cam[2]:.3f} meters in camera frame")
        coords_odom = transform_cam_to_odom(
            (coords_cam[0], coords_cam[1], coords_cam[2]),
            (0., 0., 0.),  # example. Use actual robot pose in real application
        )
        print(f"coords in odom: {coords_odom}")
finally:
    pipeline.stop()
