# WonkyBot

WonkyBot is one of the wonkiest of all bots — an autonomous differential-drive robot designed to collect colored balls from an arena and deposit them into their corresponding buckets using computer vision and SLAM-based navigation.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Software Requirements](#software-requirements)
4. [Repository Structure](#repository-structure)
5. [Installation](#installation)
6. [Calibration](#calibration)
7. [Arena Setup & Mapping](#arena-setup--mapping)
8. [Configuring Waypoints](#configuring-waypoints)
9. [Launching the Full System](#launching-the-full-system)
10. [System Architecture](#system-architecture)
11. [Color Detection Tuning](#color-detection-tuning)
12. [Troubleshooting](#troubleshooting)

---

## Project Overview

WonkyBot performs a fully autonomous ball-sorting routine:

1. Navigates to a pre-mapped ball approach waypoint using Nav2 + AMCL localization
2. Hands off to a vision node for fine approach using proportional camera-based steering
3. Commands the arm to grab the ball once within range
4. Navigates to the corresponding bucket waypoint
5. Commands the arm to release the ball
6. Returns home and repeats for additional balls

The robot uses a RealSense D455 depth camera as both its obstacle sensor (via depth-to-laserscan conversion) and its ball detector (via HSV color masking).

---

## Hardware Requirements

| Component | Description |
|-----------|-------------|
| Raspberry Pi 5 | Onboard computer running ROS 2 Jazzy |
| Raspberry Pi Pico | Microcontroller handling wheel motor PWM and encoder feedback |
| Intel RealSense D455 | RGB-D camera for obstacle avoidance and ball detection |
| Differential Drive Chassis | 4-wheel chassis with rear-wheel drive |
| Drive Motors | DC gear motors with quadrature encoders (70:1 ratio) |
| Arm/Gripper | Servo-actuated grabber controlled by Pico |

**Key physical measurements (update after measuring your robot):**

| Parameter | Value | Location |
|-----------|-------|----------|
| Tire diameter | 6.3 inches (0.160 m) | `picoscripts/wheel_driver.py` → `WHEEL_RADIUS` |
| Wheel separation | ~16 inches (0.406 m) | `picoscripts/diff_drive_controller.py` → `WHEEL_SEP` |
| Camera offset from base_link | x=0.43 m, z=0.10 m | `start_nav.sh` → Tab 2 static transform |

---

## Software Requirements

- **OS:** Ubuntu 24.04 (or compatible) on Raspberry Pi 5
- **ROS 2:** Jazzy Jalisco
- **Nav2:** `nav2-bringup`, `nav2-simple-commander`
- **RealSense ROS:** `realsense2_camera`
- **Python packages:** `pyserial`, `opencv-python`, `numpy`, `cv_bridge`
- **ROS packages:** `depthimage_to_laserscan`, `tf2_ros`, `tf_transformations`
- **DDS middleware:** `rmw-cyclonedds-cpp`

Install ROS 2 dependencies:
```bash
sudo apt install ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander \
    ros-jazzy-realsense2-camera ros-jazzy-depthimage-to-laserscan \
    ros-jazzy-tf2-ros ros-jazzy-tf-transformations \
    ros-jazzy-rmw-cyclonedds-cpp
pip3 install pyserial opencv-python numpy
```

---

## Repository Structure

```
WonkyBot/                          ← This repository (cloned into ~/seniordesign_ws/src/)
├── solid-octo-happiness/          ← ROS 2 package: robot driver + vision + navigation nodes
│   └── solid_octo/solid_octo/
│       ├── octo_pilot.py          ← Motor driver node (Pi ↔ Pico serial)
│       ├── detector_node.py       ← Ball/bucket detection via RealSense color + depth
│       ├── sorting_master.py      ← Vision-guided approach + grab/release logic
│       ├── waypoint_navigator.py  ← Autonomous Nav2 waypoint sequence
│       └── colors.json            ← HSV color ranges for ball detection
├── solid_octo_config_nav/
│   └── config/nav2_params.yaml   ← Nav2 AMCL, MPPI controller, costmap parameters
├── picoscripts/
│   ├── wheel_driver.py            ← Pico: encoder-based velocity calculation + PID
│   ├── diff_drive_controller.py   ← Pico: differential drive kinematics
│   └── main.py                    ← Pico: main firmware entry point
├── autonomous_nav/                ← Standalone Nav2 pose navigation utility
└── README.md
```

> **Note:** `start_nav.sh` and `start_mapping.sh` are included in this repo. After cloning, copy them to your home directory so they can be run from anywhere.

---

## Installation

### 1. Clone the workspace

```bash
mkdir -p ~/seniordesign_ws/src
cd ~/seniordesign_ws/src
git clone --recurse-submodules https://github.com/efieldsUCA/WonkyBot.git .
```

### 2. Copy the launch script

```bash
cp ~/seniordesign_ws/src/start_nav.sh ~/start_nav.sh
chmod +x ~/start_nav.sh
```

### 3. Build the ROS 2 workspace

```bash
cd ~/seniordesign_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 4. Flash the Pico firmware

Open **Thonny** on the Pi or a laptop, connect to the Pico, and copy these files to the Pico's root filesystem:

- `picoscripts/main.py`
- `picoscripts/wheel_driver.py`
- `picoscripts/diff_drive_controller.py`

---

## Calibration

Before running navigation, verify two critical physical measurements.

### Wheel Radius

Measure the **outer diameter** of your drive tires. Divide by 2 for the radius.

Edit `picoscripts/wheel_driver.py`:
```python
self.WHEEL_RADIUS = 0.080  # meters — update to match your actual tire
```

### Wheel Separation

Measure **center-to-center distance** between the left and right rear wheels.

Edit `picoscripts/diff_drive_controller.py`:
```python
self.WHEEL_SEP = 0.406  # meters — update to match your measured axle width
```

> **Why this matters:** Incorrect values cause the robot to overshoot waypoints or spin incorrectly. A 10% error in wheel radius causes 10% distance error in odometry.

After editing, re-flash both files to the Pico via Thonny.

---

## Arena Setup & Mapping

Before running the autonomous sequence, you must create a map of the arena.

### Build the map (run once per arena layout)

```bash
bash ~/start_mapping.sh
```

- Manually drive the robot around the full arena using a joystick or keyboard teleop.
- When the map looks complete in RViz, save it:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/room_map
```

This creates `~/room_map.yaml` and `~/room_map.pgm`, which `start_nav.sh` loads automatically.

---

## Configuring Waypoints

After mapping, drive the robot to each ball approach point and bucket location, then record the coordinates.

### Record coordinates

With Nav2 running and the robot localized:
```bash
ros2 topic echo /amcl_pose --once
```

Read the `pose.pose.position.x`, `.y`, and the yaw from the quaternion.

### Edit waypoints

Open `solid-octo-happiness/solid_octo/solid_octo/waypoint_navigator.py` and update:

```python
BALL_WAYPOINTS = [
    (1.730, -1.152, 0.325),   # ball 1 approach — ~0.5m before the ball
    # Add more balls here
]

BUCKET_WAYPOINTS = [
    (3.387, -3.133, -2.138),  # deposit point for ball 1
    # Add matching bucket per ball above
]

HOME = (0.000, 0.000, 0.000)  # starting position
```

> **Tip:** Place ball approach waypoints approximately 0.5 m in front of the ball — sorting_master handles the final approach using the camera.

### Rebuild after editing

```bash
cd ~/seniordesign_ws
colcon build --packages-select solid_octo
source install/setup.bash
```

---

## Launching the Full System

Run the master launch script from the Pi's desktop terminal:

```bash
bash ~/start_nav.sh
```

This opens **8 terminal tabs** in sequence:

| Tab | Name | What it does |
|-----|------|--------------|
| 1 | Motors | Starts `octo_pilot` — serial communication to Pico |
| 2 | TF | Publishes static `base_link → camera_link` transform |
| 3 | Camera | Starts RealSense D455 with depth alignment enabled |
| 4 | LaserScan | Converts depth image to `/scan` for Nav2 obstacle avoidance |
| 5 | Nav2 | Launches Nav2 bringup with map and parameters |
| 6 | Lifecycle | Activates all Nav2 lifecycle nodes in order |
| 7 | Relay | Bridges `/cmd_vel_nav → /cmd_vel` so Nav2 commands reach the motors |
| 8 | Waypoints | Waits 30 s for Nav2, then starts the autonomous ball-sorting sequence |

### Wait for readiness

Watch **Tab 6**. When it prints:
```
✓ ALL LIFECYCLE NODES ACTIVE
```
the robot will begin navigating automatically within a few seconds.

### Setting initial pose (first run)

On the first run, the robot starts at the arena origin `(0, 0, 0)`. If the robot is not physically at the origin when you run the script, you must set its initial pose in RViz:

1. Open RViz on a laptop connected to the same network (set `ROS_DOMAIN_ID` to match the Pi).
2. Click **"2D Pose Estimate"** and click the robot's actual location on the map.

---

## System Architecture

```
                    ┌─────────────────────────────────────────────────┐
                    │              Raspberry Pi 5                     │
                    │                                                 │
  RealSense D455 ──▶│  detector_node ──▶ /detected_objects           │
                    │                          │                      │
                    │  waypoint_navigator ◀────┘                      │
                    │       │  /vision_activate                       │
                    │       ▼                                         │
                    │  sorting_master ──▶ /arm_command                │
                    │       │  /cmd_vel                               │
                    │       ▼                                         │
  Pico (serial) ◀──│  octo_pilot ◀── /cmd_vel                        │
                    │                                                 │
  Depth → /scan ───▶│  Nav2 (AMCL + MPPI) ──▶ /cmd_vel_nav ──relay──▶/cmd_vel
                    └─────────────────────────────────────────────────┘
```

**Key topics:**

| Topic | Type | Purpose |
|-------|------|---------|
| `/cmd_vel` | `Twist` | Final velocity command to robot |
| `/cmd_vel_nav` | `Twist` | Nav2's velocity output (relayed to `/cmd_vel`) |
| `/odom` | `Odometry` | Wheel odometry from Pico encoder data |
| `/scan` | `LaserScan` | Obstacle scan from depth image |
| `/detected_objects` | `String` (JSON) | Ball/bucket detections with depth |
| `/vision_activate` | `Bool` | waypoint_navigator → sorting_master handoff |
| `/grab_complete` | `Bool` | sorting_master → waypoint_navigator grab confirmation |
| `/arm_command` | `String` | `"GRAB"` or `"RELEASE"` to arm controller |

---

## Color Detection Tuning

Ball colors are defined in `solid-octo-happiness/solid_octo/solid_octo/colors.json`.

Each entry contains:
- `lower` / `upper`: HSV range `[H, S, V]` (OpenCV scale: H=0-179, S=0-255, V=0-255)
- `bgr`: color for debug overlay `[B, G, R]`
- `lower2` / `upper2`: optional second range (used for red, which wraps around H=0/180)

To tune colors:
1. Run `ros2 run solid_octo detector_node` while pointing the camera at a ball.
2. Watch the terminal output — it logs detections and circularity values.
3. Subscribe to `/detector/debug_image` in RViz to see the annotated frame.
4. Adjust HSV ranges in `colors.json` until only the target object is detected reliably.
5. Rebuild: `colcon build --packages-select solid_octo`

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Robot doesn't move at all | Pico not connected | Check `/dev/ttyACM0` exists: `ls /dev/ttyACM*` |
| Robot overshoots waypoints | Wrong `WHEEL_RADIUS` | Measure tire, update `wheel_driver.py`, re-flash Pico |
| Robot spins incorrectly | Wrong `WHEEL_SEP` | Measure axle width, update `diff_drive_controller.py`, re-flash |
| "Waiting 2.07m remaining" loop | Nav2 not activated yet | Wait for Tab 6 to print "ALL LIFECYCLE NODES ACTIVE" |
| Map not loading | `room_map.yaml` missing | Run `start_mapping.sh` and save map first |
| No `/scan` topic | Camera not started | Check Tab 3 (RealSense) for errors |
| Phantom obstacles everywhere | `range_min` too low | `nav2_params.yaml`: set `obstacle_min_range: 0.35` in both costmaps |
| `colors.json` not found | Package not rebuilt | `colcon build --packages-select solid_octo` |
| TF error: `base_link → camera_link` | Tab 2 crashed | Restart Tab 2 or re-run `start_nav.sh` |
| Detector sees everything as BUCKET | Low circularity | Improve lighting; lower `MIN_AREA` in `detector_node.py` |

---

## License

MIT License — see `LICENSE` for details.

---

*Built by Edward Fields — University of Central Arkansas Senior Design, Spring 2026.*
