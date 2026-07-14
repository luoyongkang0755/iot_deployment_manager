# Final Technical Report — Scout Mini Dual LiDAR Navigation System

**Author**: Student  
**Date**: 2026-07-14  
**Repository**: [scout_mini_nav2](https://github.com/luoyongkang0755/scout_mini_nav2)  
**ROS 2 Distribution**: Humble  

---

## 1. Introduction

This report documents the design, implementation, and testing of an autonomous navigation system for the AgileX Scout Mini robot. The system uses the ROS2 Humble framework, Nav2 navigation stack, and Gazebo Ignition (Fortress) simulation. Two RS-AIRY LiDAR sensors (front and rear) are simulated for 360° perception coverage.

The project was completed as a structured assignment with 28 tasks covering all phases from basic Linux commands through to a fully reproducible, well-documented navigation system with separated simulation and real-robot configurations.

---

## 2. Assignment Objectives

| Objective | Status |
|-----------|--------|
| ROS2 workspace and package creation | Completed |
| Publisher/subscriber communication | Completed |
| TF tree and coordinate frame understanding | Completed |
| Docker containerized ROS2 environment with GUI | Completed |
| Scout Mini URDF model in RViz2 and Gazebo | Completed |
| Dual RS-AIRY LiDAR simulation | Completed |
| Teleoperation and sensor validation | Completed |
| Navigation world with obstacles | Completed |
| SLAM mapping and map preparation | Completed |
| Nav2 integration (AMCL, planner, controller, BT) | Completed |
| Three-goal navigation testing (100% success) | Completed |
| Clean build reproducibility (0 errors) | Completed |
| Simulation vs. real robot config separation | Completed |
| Real robot safety checklist | Completed |
| Comprehensive README for reproducibility | Completed |

---

## 3. Repository Structure

```
scout_nav2_mini/
├── src/
│   ├── scout_mini_dual_lidar_gazebo/          # Main Nav2 + Gazebo package
│   │   ├── config/
│   │   │   ├── nav2_params.yaml               # Nav2 parameters (all nodes)
│   │   │   ├── navigate_no_init_check.xml     # Custom behavior tree
│   │   │   ├── simulation/nav2_params.yaml    # Sim-specific config
│   │   │   └── real_robot/nav2_params.yaml    # Real robot config
│   │   ├── launch/
│   │   │   ├── nav2_launch.py                 # One-click full stack
│   │   │   ├── scout_mini_gazebo.launch.py    # Gazebo only
│   │   │   ├── slam.launch.py                 # SLAM Toolbox
│   │   │   ├── simulation/                    # Sim launch files
│   │   │   └── real_robot/                    # Real robot launch files
│   │   ├── maps/                              # Pre-built SLAM maps
│   │   ├── worlds/                            # Gazebo world files
│   │   └── src/                               # Python nodes (7 scripts)
│   ├── external/scout_ros2/                   # AgileX Scout ROS2 packages
│   │   ├── scout_description/                 # URDF/XACRO models
│   │   ├── scout_msgs/                        # Custom ROS messages
│   │   └── scout_base/                        # CAN driver (real robot)
│   └── ros2_learning_examples/                # Basic publisher/subscriber
├── docker/                                    # Dockerfile + run scripts
├── reports/                                   # All task reports
├── media/                                     # Screenshots, videos, logs
├── README.md                                  # Comprehensive setup guide
└── TASK_LOG.md                                # Task-by-task log
```

---

## 4. Docker Environment

A custom Docker image based on `ros:humble-ros-base` was created to provide a fully containerized development environment. The Dockerfile includes:

- **ROS2 Humble base** with build tools (colcon, cmake)
- **Nav2** full stack (`nav2-bringup`, `nav2-amcl`, `nav2-planner`, `nav2-controller`, etc.)
- **Gazebo Ignition** (`ros-gz-sim`, `ros-gz-bridge`)
- **SLAM Toolbox** for map building
- **RViz2** + **teleop_twist_keyboard** for interaction
- **Tsinghua mirror** for apt/rosdep to accelerate build

**Build and run commands:**

```bash
docker build -t ros2_humble_minimal:latest -f docker/Dockerfile .
bash docker/run.sh
```

The container uses `--net=host` and X11 forwarding for GUI support (Gazebo + RViz2). The entrypoint automatically sources ROS2 and workspace environments.

---

## 5. Scout Mini Simulation

### URDF Model

The Scout Mini is modeled in Xacro format with:
- **Dimensions**: 600mm × 370mm × 285mm (L×W×H)
- **Wheels**: 4 wheels (145mm radius), differential drive
- **Mass**: ~22 kg
- **Gazebo plugins**: DiffDrive for motion, IMU sensor, joint state publishing

The model publishes `/robot_description` and static transforms via `robot_state_publisher`.

### Gazebo Spawning

The robot spawns at position `(0, 0, 0.181)` with configurable yaw in a 16m×16m enclosed world with 6 colored obstacle boxes and boundary walls.

| Obstacle | Position (x,y) | Size (m) | Color |
|----------|----------------|----------|-------|
| Box 1 | (4.0, 0.0) | 1.0×1.0×1.0 | Red |
| Box 2 | (0.0, 4.0) | 0.8×0.8×0.6 | Green |
| Box 3 | (0.0, -4.0) | 1.2×0.6×0.8 | Blue |
| Box 4 | (-4.0, 0.0) | 0.8×1.5×1.2 | Yellow |
| Box 5 | (3.0, 3.0) | 0.7×0.7×0.8 | Purple |
| Box 6 | (-3.0, -3.0) | 0.9×0.9×1.0 | Orange |

![Gazebo World](media/screenshots/task16_gazebo.png)

---

## 6. Dual RS-AIRY LiDAR Simulation

Two RS-AIRY LiDAR sensors were integrated into the Scout Mini URDF:

| Sensor | Position (x,y,z) | Topic | Frame ID |
|--------|-------------------|-------|----------|
| Front LiDAR | (0.245, 0, 0.14) | `/front/scan` | `front_lidar_link` |
| Rear LiDAR | (-0.245, 0, 0.14) | `/rear/scan` | `rear_lidar_link` |

### LiDAR Specifications
- **Range**: 0.1m – 25m
- **Angular resolution**: 1° (360 samples)
- **Update rate**: ~10 Hz

### Sensor Processing Pipeline

Due to Gazebo prepending model names to frame_ids, a processing pipeline was implemented:

```
Gazebo LiDAR → ros_gz_bridge → scan_frame_fixer.py → laser_merger.py → /merged/scan
```

1. **`scan_frame_fixer.py`**: Strips `scout_mini/` prefix from frame_ids
2. **`laser_merger.py`**: Merges front and rear scans into a single 360° `/merged/scan` topic

### Frequency Verification

```
$ ros2 topic hz /front/scan
average rate: 9.894 Hz

$ ros2 topic hz /rear/scan
average rate: 9.876 Hz
```

![Dual LiDAR in RViz2](media/screenshots/task15.png)

---

## 7. TF Tree and ROS Topics

### TF Tree Structure

```
map
 └── odom
      └── base_link
           ├── front_lidar_link
           └── rear_lidar_link
```

- `map → odom`: Provided by AMCL localization (corrects odometry drift)
- `odom → base_link`: Real-time odometry from Gazebo DiffDrive (via `odom_to_tf.py`)
- `base_link → front_lidar_link` / `rear_lidar_link`: Static transforms from URDF

![TF Tree](media/screenshots/task18_tf.png)

### Key ROS Topics

| Topic | Type | Publisher | Function |
|-------|------|-----------|----------|
| `/front/scan` | LaserScan | ros_gz_bridge | Front LiDAR data |
| `/rear/scan` | LaserScan | ros_gz_bridge | Rear LiDAR data |
| `/merged/scan` | LaserScan | laser_merger | Fused 360° scan |
| `/cmd_vel` | Twist | teleop / Nav2 | Velocity commands |
| `/odom` | Odometry | odom_to_tf | Corrected odometry |
| `/map` | OccupancyGrid | map_server | Static environment map |
| `/plan` | Path | planner_server | Global path |
| `/local_plan` | Path | controller_server | Local trajectory |
| `/amcl_pose` | PoseWithCovariance | AMCL | Localized robot pose |
| `/tf` | TFMessage | robot_state_publisher, AMCL, odom_to_tf | Coordinate transforms |

---

## 8. Map Preparation

A pre-built SLAM map (`my_map.yaml` / `my_map.pgm`) is used for localization and navigation. The map was generated by driving the robot through the Gazebo world while running SLAM Toolbox, then saved with `map_saver_cli`.

**Map properties:**

| Property | Value |
|----------|-------|
| Format | PGM (Portable Gray Map) |
| Resolution | 0.05 m/pixel |
| Size | ~16m × 16m |
| Origin | (-8.38, -8.01) |
| Occupancy threshold | 0.65 |
| Free threshold | 0.25 |

**SLAM workflow:**

```bash
# Launch Gazebo
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# Launch SLAM
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py

# Drive and explore
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Save map
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

---

## 9. Nav2 Configuration

### Nodes Deployed

| Node | Package | Function |
|------|---------|----------|
| `map_server` | nav2_map_server | Serves static occupancy grid map |
| `amcl` | nav2_amcl | Adaptive Monte Carlo Localization |
| `planner_server` | nav2_planner | Global path planning (NavFn/A*) |
| `controller_server` | nav2_controller | Local path following (DWB) |
| `bt_navigator` | nav2_bt_navigator | Behavior tree engine |
| `recoveries_server` | nav2_behaviors | Spin/backup/wait recovery |
| `waypoint_follower` | nav2_waypoint_follower | Waypoint sequence execution |
| `lifecycle_manager` | nav2_lifecycle_manager | Auto-activation of all nodes |

### Global Planner: NavFn

- Grid-based A* search
- Tolerance: 0.5m
- Unknown space allowed for exploration

### Local Controller: DWB (Dynamic Window Approach)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `max_vel_x` | 0.5 m/s | Forward speed limit |
| `max_vel_theta` | 1.0 rad/s | Rotation speed limit |
| `min_vel_x` | 0.0 m/s | Allows pure rotation near goals |
| `min_speed_xy` | 0.0 | Enables zero-velocity trajectories |
| `xy_goal_tolerance` | 0.25 m | Position tolerance |
| `yaw_goal_tolerance` | 0.5 rad | Heading tolerance |
| `sim_time` | 1.7 s | Trajectory simulation horizon |
| `vx_samples` | 20 | Linear velocity samples |
| `vtheta_samples` | 20 | Angular velocity samples |

**Critics (scoring functions):**
- `RotateToGoal`, `Oscillation`, `BaseObstacle`
- `GoalAlign`, `PathAlign`, `PathDist`, `GoalDist`

### Behavior Tree

A custom behavior tree (`navigate_no_init_check.xml`) was created to bypass the `InitialPoseReceived` condition (which is not automatically set in current Nav2 versions). The BT includes proper blackboard port bindings for `goal` and `path` data flow between nodes.

### Costmap Configuration

| Layer | Local | Global |
|-------|-------|--------|
| Size | 3m × 3m rolling | Static map bounds |
| Resolution | 0.05 m/pixel | 0.05 m/pixel |
| Robot radius | 0.3 m | 0.3 m |
| Inflation radius | 0.55 m | 0.55 m |
| Update frequency | 5 Hz | 1 Hz |

---

## 10. Navigation Test Results

### Three-Goal Test

The system was verified using a script that sends three sequential navigation goals via the `/navigate_to_pose` action server.

**Final Test Results:**

| Test | Start | Goal | Result | Time | Collision | Notes |
|------|-------|------|--------|------|-----------|-------|
| 1 | (0,0,0) | (2.0, 0.0, 0.0) | **Success** | ~4s | No | Straight-line path |
| 2 | (0,0,0) | (-2.0, 2.0, 0.0) | **Success** | ~15s | No | Diagonal with obstacle avoidance |
| 3 | (0,0,0) | (2.0, -2.0, 0.0) | **Success** | ~14s | No | Diagonal with goal rotation |

**Success rate: 100% (3/3)**

![Goal 1 — RViz2](media/screenshots/task%2022%20goal%201.png)
![Goal 2 — RViz2](media/screenshots/task22%20goal2.png)
![Goal 3 — RViz2](media/screenshots/task22%20goal3.png)

**Video**: [media/task22 vedio.webm](media/task22%20vedio.webm)

### Nav2 Terminal Log (Excerpt)

```
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
[bt_navigator] Begin navigating from current location (1.77, -0.02) to (-2.00, 2.00)
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
[bt_navigator] Begin navigating from current location (-1.94, 1.95) to (2.00, -2.00)
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
```

Full log: [media/LOG/task22.log](media/LOG/task22.log)

---

## 11. Issues and Fixes

### Issue 1: Behavior Tree Stuck on InitialPoseReceived

**Symptom**: Robot accepted goal but never started path planning. Behavior tree stuck at `InitialPoseReceived` condition.

**Root Cause**: The `initial_pose_received` blackboard variable is not automatically set in newer Nav2 versions.

**Fix**: Created `navigate_no_init_check.xml` that removes the `InitialPoseReceived` check, allowing `ComputePathToPose` to execute directly.

### Issue 2: Blackboard Port Bindings Missing

**Symptom**: `ComputePathToPose` and `FollowPath` nodes couldn't share `goal` and `path` data.

**Fix**: Added explicit port bindings: `goal="{goal}"`, `path="{path}"`, `planner_id="GridBased"`, `controller_id="FollowPath"`.

### Issue 3: Goal Oscillation and Timeout

**Symptom**: Robot reached ~0.15m from goal but oscillated indefinitely (42–44s), then goal was canceled. Error: `"No valid trajectories out of 420!"` / `"RotateToGoal/Nonrotation command near goal"`.

**Root Cause**: Three interacting parameter issues:

| Fix | Before | After | Effect |
|-----|--------|-------|--------|
| `RotateToGoal.lookahead_time` | -1.0 | 1.0 | Enabled proper rotation trajectory evaluation |
| `min_vel_x` / `min_speed_xy` | 0.05 | 0.0 | Allowed pure-rotation trajectories near goals |
| `yaw_goal_tolerance` | 0.25 rad | 0.5 rad | Reduced convergence difficulty for differential drive |
| `required_movement_radius` | 0.5 m | 0.1 m | Prevented false "stuck" detection during fine approach |
| `movement_time_allowance` | 10.0 s | 15.0 s | Gave more time for goal-convergence micro-adjustments |

**Result**: After applying all five fixes, all three goals converged successfully with no oscillation.

### Issue 4: Gazebo Frame ID Prefix

**Symptom**: LiDAR data had `frame_id: scout_mini/base_link/front_lidar_sensor`, not matching URDF links.

**Fix**: Created `scan_frame_fixer.py` to strip the `scout_mini/` prefix and republish scans with correct frame_ids.

### Issue 5: Odometry Not Publishing TF

**Symptom**: Gazebo DiffDrive plugin publishes odometry via Gazebo topic, not ROS `/odom`.

**Fix**: Bridged `/odom_raw` from Gazebo, added `imu_odom_corrector.py` to fuse IMU angular velocity, and `odom_to_tf.py` to publish `odom → base_link` TF.

---

## 12. Limitations

1. **Goal convergence time**: The differential-drive DWB controller can take 10–44s to converge near goals, especially on diagonal paths. This is inherent to the algorithm's xy+yaw dual-tolerance checking on non-holonomic platforms.

2. **Gazebo frame_id behavior**: Gazebo prepends model names to sensor frame_ids, requiring the `scan_frame_fixer.py` workaround. This is not needed on the real robot.

3. **Map dependency**: Navigation requires a pre-built static map. If the Gazebo world changes, SLAM must be re-run.

4. **Single LiDAR on real robot**: The simulation uses dual merged LiDAR for 360° coverage. The real robot configuration defaults to single front LiDAR and would need `laser_merger.py` updated for dual LiDAR if available.

5. **Docker networking**: The container uses `--net=host` for DDS discovery. This works on standard Linux hosts but may not work behind certain firewalls or VPNs.

6. **Performance overhead**: Running Gazebo + Nav2 + RViz2 simultaneously consumes significant CPU/GPU. On low-resource machines, consider running RViz2 outside the container.

---

## 13. Physical Robot Test Preparation

The repository includes separated configurations and a comprehensive checklist for real robot deployment.

### Configuration Separation

| Aspect | Simulation | Real Robot |
|--------|-----------|------------|
| Time source | `use_sim_time: True` | `use_sim_time: False` |
| Scan topic | `/merged/scan` | `/front/scan` |
| Velocity limits | 0.5 m/s, 1.0 rad/s | 0.3 m/s, 0.5 rad/s |
| Launch file | `nav2_simulation_launch.py` | `nav2_real_robot_launch.py` |
| Config file | `config/simulation/nav2_params.yaml` | `config/real_robot/nav2_params.yaml` |

### Deployment Checklist (6 Phases)

| Phase | Focus | Key Items |
|-------|-------|-----------|
| 1 | Safety | E-stop verification, battery check, robot lifted |
| 2 | Communication | CAN interface (`can0` at 500kbps), LiDAR IP addresses |
| 3 | Validation | TF tree, odometry, LiDAR data quality (no movement) |
| 4 | Motor test | `cmd_vel` test lifted, then ground contact at 0.05 m/s |
| 5 | Nav2 test | Straight line → turn-in-place → multi-point (obstacle-free) |
| 6 | Shutdown | Node teardown, CAN down, battery disconnect |

8 emergency stop criteria defined. Full checklist: [`reports/real_robot_testing_checklist.md`](reports/real_robot_testing_checklist.md).

---

## 14. Conclusion

This project successfully implemented an autonomous navigation system for the Scout Mini robot using ROS2 Humble and the Nav2 framework.

### Key Achievements

- **Full simulation pipeline**: One-command launch starts Gazebo world, Scout Mini robot with dual LiDAR, Nav2 navigation stack, and RViz2 visualization.
- **Proven navigation performance**: Three-point navigation test achieved 100% success rate (3/3 goals reached).
- **Parameter tuning**: Five DWB controller parameters were optimized to resolve goal-convergence oscillation issues specific to differential-drive platforms.
- **Clean build reproducibility**: All 6 packages build from scratch in 1.22s with zero errors — no undocumented manual steps required.
- **Real robot readiness**: Separated simulation and real robot configurations, comprehensive 6-phase deployment checklist, conservative velocity limits for first physical tests.
- **Complete documentation**: Final README covers all steps from Docker setup through navigation testing with troubleshooting and known limitations documented.

### System Verification Summary

| Metric | Result |
|--------|--------|
| Packages built | 6/6 (100%) |
| Clean build time | 1.22s |
| Navigation success rate | 3/3 (100%) |
| Goal 1 time | ~4s |
| Goal 2 time | ~15s |
| Goal 3 time | ~14s (tuned) |
| LiDAR frequency | ~10 Hz (both sensors) |
| TF tree integrity | Verified correct |
| Config separation | Simulation + real robot |
| Documentation completeness | 13-section README + 6 task reports |

### Evidence Summary

| Evidence | Path |
|----------|------|
| Gazebo screenshot | `media/screenshots/task16_gazebo.png` |
| RViz2 screenshots (3 goals) | `media/screenshots/task22 goal*.png` |
| TF tree | `media/screenshots/task18_tf.png` |
| Dual LiDAR visualization | `media/screenshots/task15.png` |
| Navigation video | `media/task22 vedio.webm` |
| Three-goal terminal log | `media/LOG/task22.log` |
| System architecture diagram | In this report and README |
| Topic list | This report (Section 7) |

The system is ready for deployment on a physical Scout Mini robot following the checklist in [`reports/real_robot_testing_checklist.md`](reports/real_robot_testing_checklist.md).

---

*End of Report*
