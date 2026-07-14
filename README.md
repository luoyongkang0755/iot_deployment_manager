# Scout Mini Dual LiDAR Navigation2 (ROS2)

## Project Overview

This project implements autonomous navigation for the AgileX **Scout Mini** robot using **ROS2 Humble** and the **Nav2** framework. It supports both Gazebo simulation (with full physics and sensor emulation) and future physical robot deployment.

**Key capabilities:**
- Dual RS-AIRY LiDAR simulation (front + rear) with 360° merged scan
- AMCL localization with a pre-built SLAM map
- DWB local planner with tuned parameters for goal convergence
- Behavior tree-based navigation with recovery behaviors
- One-command launch for the entire stack (Gazebo + robot + Nav2 + RViz2)
- Separated simulation and real robot configurations

---

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                    RViz2                        │
│         (visualization & goal input)            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                 Nav2 Stack                       │
│  ┌─────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ map_    │  │ planner_  │  │ controller_   │  │
│  │ server  │  │ server    │  │ server (DWB)  │  │
│  └─────────┘  └──────────┘  └───────────────┘  │
│  ┌─────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ AMCL    │  │ bt_       │  │ recoveries_   │  │
│  │         │  │ navigator │  │ server        │  │
│  └─────────┘  └──────────┘  └───────────────┘  │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Sensor Processing                   │
│  ┌────────────┐  ┌───────────┐  ┌────────────┐ │
│  │ laser_     │  │ imu_odom   │  │ odom_to_tf │ │
│  │ merger     │  │ corrector  │  │            │ │
│  └────────────┘  └───────────┘  └────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│            Gazebo Simulation                      │
│  ┌─────────────────────────────────────────┐    │
│  │  Scout Mini URDF + DiffDrive plugin      │    │
│  │  Front LiDAR (0.245m) + Rear LiDAR       │    │
│  │  ros_gz_bridge (clock, cmd_vel, scans)   │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

**TF Tree:** `map → odom → base_link → front_lidar_link / rear_lidar_link`

---

## Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Containerized ROS 2 environment |
| ROS 2 | Humble | Robot middleware |
| Gazebo | Ignition (Fortress) | Physics simulation |
| Nav2 | Humble | Navigation stack |
| SLAM Toolbox | Humble | SLAM map building |
| Python | 3.10+ | Node scripting |

---

## Docker Build Instructions

### Prerequisites (Host — Ubuntu 22.04)

```bash
sudo apt-get update
sudo apt-get install -y x11-xserver-utils docker.io
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
xhost +local:docker
```

### Build the Docker Image

```bash
cd ~/scout_nav2_mini
docker build -t ros2_humble_minimal:latest -f docker/Dockerfile .
```

This installs ROS2 Humble, Nav2, Gazebo, SLAM Toolbox, and all dependencies (~10-15 minutes).

---

## Docker Run Instructions

```bash
cd ~/scout_nav2_mini
bash docker/run.sh
```

This mounts `src/` into the container at `/ws/src`, enables GUI (X11 forwarding), and drops you into a bash shell inside `/ws`. The entrypoint automatically sources ROS2 and workspace environments.

**If you see "rviz2: command not found"**, rebuild the image:
```bash
docker build -t ros2_humble_minimal:latest -f docker/Dockerfile .
```

---

## Workspace Build Instructions

Inside the Docker container:

```bash
cd /ws
colcon build --symlink-install
source install/setup.bash
```

**Expected output:**
```
Summary: 6 packages finished [~1.2s]
  scout_msgs              [Success]
  scout_description       [Success]
  scout_mini_dual_lidar_gazebo [Success]
  ros2_learning_examples  [Success]
  ugv_sdk                 [Success]
  scout_base              [Success]
```

---

## Simulation Launch Commands

### Option A: One-Click Nav2 Full Stack

```bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py
```

Launches everything: Gazebo world, Scout Mini robot, dual LiDAR, all Nav2 nodes, and RViz2.

### Option B: Gazebo Only (without Nav2 — for remote control or SLAM)

```bash
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py
```

### Option C: Simulation Nav2 (using separated config)

```bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_simulation_launch.py
```

---

## Teleoperation Commands

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

| Key | Action |
|-----|--------|
| `i` | Forward |
| `k` | Backward |
| `j` | Turn left |
| `l` | Turn right |
| `space` | Stop |
| `q/z` | Speed up/down |

---

## Mapping Commands (SLAM)

### Step 1: Launch Gazebo

```bash
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py
```

### Step 2: Launch SLAM Toolbox

```bash
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py
```

### Step 3: Drive the robot to explore the environment

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Step 4: Save the map

```bash
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

---

## Nav2 Launch Commands

### Simulation (with Gazebo)

```bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py
```

This starts all Nav2 nodes: `map_server`, `amcl`, `planner_server`, `controller_server`, `bt_navigator`, `recoveries_server`, `waypoint_follower`, `lifecycle_manager`, and RViz2.

**After launch:**
1. In RViz2, use **"2D Pose Estimate"** to set the robot's initial position on the map.
2. Use **"Nav2 Goal"** to send a navigation target.
3. Watch the robot plan and execute the path.

### Real Robot (no Gazebo)

```bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_real_robot_launch.py
```

Requires `scout_base` driver and LiDAR drivers running separately. See "Real Robot Preparation" below.

---

## Three-Goal Point Test

```bash
ros2 run scout_mini_dual_lidar_gazebo send_nav2_goals.py
```

Sends 3 goals sequentially:
1. `(2.0, 0.0, 0.0)` — straight line
2. `(-2.0, 2.0, 0.0)` — diagonal with obstacle avoidance
3. `(2.0, -2.0, 0.0)` — diagonal

Results are printed as a formatted table. **To customize goals**, edit the `GOALS` list at the top of `src/scout_mini_dual_lidar_gazebo/src/send_nav2_goals.py`.

---

## Project Structure

```
scout_nav2_mini/
├── src/
│   └── scout_mini_dual_lidar_gazebo/
│       ├── config/
│       │   ├── nav2_params.yaml
│       │   ├── navigate_no_init_check.xml
│       │   ├── simulation/
│       │   │   └── nav2_params.yaml          # Sim: use_sim_time=True, /merged/scan
│       │   └── real_robot/
│       │       └── nav2_params.yaml          # Real: use_sim_time=False, /front/scan
│       ├── launch/
│       │   ├── nav2_launch.py                # One-click: Gazebo + Nav2 + RViz
│       │   ├── scout_mini_gazebo.launch.py   # Gazebo only
│       │   ├── slam.launch.py                # SLAM Toolbox
│       │   ├── simulation/
│       │   │   └── nav2_simulation_launch.py
│       │   └── real_robot/
│       │       └── nav2_real_robot_launch.py
│       ├── maps/
│       │   └── my_map.yaml / my_map.pgm
│       ├── worlds/
│       │   └── simple_test_world.world
│       └── src/
│           ├── send_nav2_goals.py            # Three-goal test script
│           ├── laser_merger.py               # Dual LiDAR → /merged/scan
│           ├── odom_to_tf.py                 # Odom → TF publisher
│           ├── imu_odom_corrector.py         # IMU + odometry fusion
│           └── scan_frame_fixer.py           # Gazebo frame_id fixer
├── docker/
│   ├── Dockerfile
│   ├── run.sh
│   └── ros_entrypoint.sh
├── reports/
│   ├── nav2_three_goal_results.md            # Task 22 test results
│   ├── clean_build_test.md                   # Task 24 build test
│   ├── simulation_vs_real_robot.md           # Task 25 config separation
│   └── real_robot_testing_checklist.md       # Task 26 safety checklist
├── media/
│   ├── screenshots/
│   └── LOG/
├── README.md
└── TASK_LOG.md
```

---

## Troubleshooting

### "No module named rclpy" or import errors

```bash
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash
```

### Robot doesn't move after sending a goal

Check the controller_server logs. Common causes:
- `"No valid trajectories"` — adjust DWB parameters (`min_vel_x`, `min_speed_xy` in nav2_params.yaml)
- `"Goal failed"` after timeout — check `required_movement_radius` and `movement_time_allowance`
- AMCL not converged — ensure initial pose is set in RViz2 via "2D Pose Estimate"

### Robot oscillates near the goal

Increase `xy_goal_tolerance` and `yaw_goal_tolerance` in nav2_params.yaml. Ensure `RotateToGoal.lookahead_time` is positive (not -1.0).

### Gazebo / GUI not opening in Docker

```bash
# On host machine (before running Docker):
xhost +local:docker

# Inside container, verify DISPLAY:
echo $DISPLAY    # should show :0 or similar
```

### "Package not found" when launching

```bash
colcon build --symlink-install
source install/setup.bash
```

### Clean rebuild

```bash
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

---

## Known Limitations

1. **DWB goal convergence**: The differential-drive platform can oscillate near goals (0.05–0.2m range) before satisfying xy + yaw tolerances. This is inherent to the DWB algorithm and has been mitigated via parameter tuning. Goal 3 in the three-point test may take up to 45s in worst case.

2. **Gazebo frame_id prefix**: Gazebo prepends `scout_mini/` to sensor frame_ids. The `scan_frame_fixer.py` node strips this prefix. This is not needed on the real robot.

3. **Map dependency**: The Nav2 stack requires a pre-built map (`my_map.yaml/pgm`). If the Gazebo world changes, a new map must be generated via SLAM.

4. **Single front LiDAR on real robot**: The simulation uses dual LiDAR with merged scans. The real robot config defaults to a single front LiDAR (`/front/scan`). Update `scan_topic` in `config/real_robot/nav2_params.yaml` if dual LiDAR is available.

5. **Docker network mode**: The container uses `--net=host` for ROS 2 DDS discovery. This may not work in all network configurations.

6. **Performance**: Running Gazebo, Nav2, and RViz2 together requires significant GPU/CPU resources. On low-resource machines, consider running RViz2 outside the container.

---

## Real Robot Preparation

For deploying on a physical Scout Mini, follow the checklist in [`reports/real_robot_testing_checklist.md`](reports/real_robot_testing_checklist.md).

**Quick reference:**

```bash
# 1. Bring up CAN interface
sudo ip link set can0 up type can bitrate 500000

# 2. Launch Scout Mini base driver
ros2 launch scout_base scout_mini_base.launch.py

# 3. Launch LiDAR driver (vendor-specific)
ros2 run urg_node urg_node_driver

# 4. Launch Nav2 (real robot config)
ros2 launch scout_mini_dual_lidar_gazebo nav2_real_robot_launch.py
```

**Key differences from simulation:**
- `use_sim_time: False`
- No Gazebo bridges, frame fixers, or IMU correctors
- Scan topic: `/front/scan` (not `/merged/scan`)
- Conservative velocities: 0.3 m/s linear, 0.5 rad/s angular
- Physical E-stop must be tested before any autonomous operation
- See [`reports/simulation_vs_real_robot.md`](reports/simulation_vs_real_robot.md) for full details
