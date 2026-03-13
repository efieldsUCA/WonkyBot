#!/bin/bash
# ─────────────────────────────────────────────────────────────
# MASTER NAVIGATION LAUNCH
# Starts all nodes needed for autonomous navigation with Nav2
#
# USAGE:
#   bash ~/start_nav.sh
#
# AFTER LAUNCH:
#   Wait for Tab 6 to print "ALL LIFECYCLE NODES ACTIVE"
#   then go to RViz:
#   1. Click "2D Pose Estimate" → click where robot is on map
#   2. Click "Nav2 Goal" → click destination
# ─────────────────────────────────────────────────────────────

WORKSPACE=~/seniordesign_ws
MAP_PATH=~/room_map.yaml
PARAMS_PATH=$WORKSPACE/src/solid_octo_config_nav/config/nav2_params.yaml

source /opt/ros/jazzy/setup.bash
source $WORKSPACE/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

echo "════════════════════════════════════════"
echo "   NAVIGATION LAUNCH PREFLIGHT CHECK"
echo "════════════════════════════════════════"

if [ ! -f "$MAP_PATH" ]; then
  echo ""
  echo "  ✗ ERROR: Map not found at $MAP_PATH"
  echo "    Run start_mapping.sh first and save your map."
  echo ""
  exit 1
fi

if [ ! -f "$PARAMS_PATH" ]; then
  echo ""
  echo "  ✗ ERROR: nav2_params.yaml not found at $PARAMS_PATH"
  echo ""
  exit 1
fi

echo "  ✓ Map found:    $MAP_PATH"
echo "  ✓ Params found: $PARAMS_PATH"
echo ""
echo "Starting all nodes..."
echo ""

# ── Tab 1: Motors ────────────────────────────────────────────
echo "[1/7] Starting motors..."
gnome-terminal --tab --title="1. Motors" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- MOTORS ---'
  ros2 launch solid_octo octo_launch.py
  exec bash"

sleep 2

# ── Tab 2: TF Transform ──────────────────────────────────────
echo "[2/7] Starting TF transform..."
gnome-terminal --tab --title="2. TF" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- TF TRANSFORM ---'
  ros2 run tf2_ros static_transform_publisher 0.43 0 0.10 0 0 0 base_link camera_link
  exec bash"

sleep 1

# ── Tab 3: Camera ────────────────────────────────────────────
echo "[3/7] Starting RealSense camera..."
gnome-terminal --tab --title="3. Camera" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- REALSENSE CAMERA ---'
  ros2 launch realsense2_camera rs_launch.py align_depth.enable:=true
  exec bash"

sleep 3

# ── Tab 4: Depth → LaserScan ─────────────────────────────────
echo "[4/7] Starting depth to laserscan..."
gnome-terminal --tab --title="4. LaserScan" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- DEPTH TO LASERSCAN ---'
  ros2 run depthimage_to_laserscan depthimage_to_laserscan_node \
    --ros-args \
    -p output_frame:=camera_link \
    -p range_min:=0.35 \
    -p range_max:=4.0 \
    -r depth:=/camera/camera/depth/image_rect_raw \
    -r depth_camera_info:=/camera/camera/depth/camera_info
  exec bash"

sleep 2

# ── Tab 5: Nav2 ──────────────────────────────────────────────
echo "[5/7] Starting Nav2 (autostart:=False)..."
gnome-terminal --tab --title="5. Nav2" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- NAV2 ---'
  ros2 launch nav2_bringup bringup_launch.py \
    map:=$MAP_PATH \
    params_file:=$PARAMS_PATH \
    use_sim_time:=False \
    autostart:=False
  exec bash"

sleep 3

# ── Tab 6: Lifecycle Activation ──────────────────────────────
echo "[6/7] Starting lifecycle activation..."
gnome-terminal --tab --title="6. Lifecycle" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- LIFECYCLE ACTIVATION ---'
  echo 'Waiting for Nav2 to finish starting...'
  sleep 8

  echo ''
  echo 'Step 1/3: Localization...'
  ros2 lifecycle set /map_server configure
  ros2 lifecycle set /amcl configure
  ros2 lifecycle set /map_server activate
  ros2 lifecycle set /amcl activate

  echo 'Setting initial pose at origin...'
  ros2 topic pub -1 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
    \"{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}}\"

  echo ''
  echo 'Step 2/3: Configuring servers...'
  ros2 lifecycle set /controller_server configure
  ros2 lifecycle set /planner_server configure
  ros2 lifecycle set /behavior_server configure
  ros2 lifecycle set /smoother_server configure
  ros2 lifecycle set /waypoint_follower configure
  # velocity_smoother and collision_monitor NOT activated —
  # they compete with the cmd_vel relay and block robot motion

  echo ''
  echo 'Step 3/3: Activating servers...'
  ros2 lifecycle set /controller_server activate
  ros2 lifecycle set /planner_server activate
  ros2 lifecycle set /behavior_server activate
  ros2 lifecycle set /smoother_server activate
  ros2 lifecycle set /waypoint_follower activate

  echo 'Activating navigator...'
  ros2 lifecycle set /bt_navigator configure
  ros2 lifecycle set /bt_navigator activate

  echo ''
  echo '══════════════════════════════════════'
  echo '  ✓ ALL LIFECYCLE NODES ACTIVE'
  echo '  Nav2 is fully ready.'
  echo '  1. Set 2D Pose Estimate in RViz'
  echo '  2. Send a Nav2 Goal'
  echo '══════════════════════════════════════'
  exec bash"

sleep 2

# ── Tab 7: cmd_vel relay ─────────────────────────────────────

echo "[7/7] Starting cmd_vel relay..."
gnome-terminal --tab --title="7. Relay" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- CMD_VEL RELAY ---'
  python3 -c \"
import rclpy
from geometry_msgs.msg import Twist
rclpy.init()
node = rclpy.create_node('cmd_vel_relay')
pub  = node.create_publisher(Twist, '/cmd_vel', 10)
sub  = node.create_subscription(Twist, '/cmd_vel_nav', lambda m: pub.publish(m), 10)
print('Relay running: /cmd_vel_nav → /cmd_vel')
rclpy.spin(node)
\"
  exec bash"

# ── Tab 8: Waypoint Navigator ────────────────────────────────
echo "[8/8] Starting waypoint navigator..."
gnome-terminal --tab --title="8. Waypoints" -- bash -c "
  source /opt/ros/jazzy/setup.bash
  source $WORKSPACE/install/setup.bash
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  echo '--- WAYPOINT NAVIGATOR ---'
  echo 'Waiting for Nav2 lifecycle to complete (30s)...'
  sleep 30
  echo 'Launching waypoint navigator...'
  ros2 run solid_octo waypoint_navigator
  exec bash"

# ── Detector + Sorting disabled — navigation first ───────────
# Uncomment both blocks below when navigation is reliable
# gnome-terminal --tab --title="9. Detector" -- bash -c "
#   source /opt/ros/jazzy/setup.bash
#   source $WORKSPACE/install/setup.bash
#   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
#   sleep 5
#   ros2 run solid_octo detector_node
#   exec bash"
# gnome-terminal --tab --title="10. Sorting" -- bash -c "
#   source /opt/ros/jazzy/setup.bash
#   source $WORKSPACE/install/setup.bash
#   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
#   ros2 run solid_octo sorting_master
#   exec bash"

echo ""
echo "════════════════════════════════════════"
echo "   ALL 10 NODES LAUNCHED"
echo "════════════════════════════════════════"
echo ""
echo "Wait for Tab 6 to print 'ALL LIFECYCLE NODES ACTIVE'"
echo "Tab 8 will auto-launch waypoint navigator after 30s."
echo ""
echo "NEXT STEPS (first run — set your waypoints):"
echo "  1. Edit waypoint_navigator.py WAYPOINTS list with arena coords"
echo "  2. Rebuild: cd ~/seniordesign_ws && colcon build --packages-select solid_octo"
echo "  3. Rerun start_nav.sh"
echo ""
echo "TO GET WAYPOINT COORDS:"
echo "  Run RViz on laptop, use '2D Pose Estimate' to see map coords"
echo "  Or: ros2 topic echo /amcl_pose  (while manually driving robot)"
echo ""
echo "TROUBLESHOOTING:"
echo "  Robot not moving  → check Tab 1 (motors) for errors"
echo "  Map not showing   → check Tab 5 (Nav2) for errors"
echo "  TF errors         → check Tab 2 (TF) is still running"
echo "  No laser scan     → check Tab 4, run: ros2 topic hz /scan"
echo "  Lifecycle failed  → check Tab 6 for which node errored"
echo ""

wait
