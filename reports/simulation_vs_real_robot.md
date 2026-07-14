# Simulation vs Real Robot Configuration Report

## Overview

This report explains the differences between the simulation and real robot configurations for Scout Mini Nav2 navigation, what can be reused, and what must change for physical deployment.

---

## Directory Structure

```
src/scout_mini_dual_lidar_gazebo/
├── config/
│   ├── simulation/
│   │   └── nav2_params.yaml          # Simulation Nav2 parameters
│   └── real_robot/
│       └── nav2_params.yaml          # Real robot Nav2 parameters
├── launch/
│   ├── simulation/
│   │   └── nav2_simulation_launch.py # Full stack: Gazebo + robot + Nav2
│   └── real_robot/
│       └── nav2_real_robot_launch.py # Nav2 only (drivers run separately)
```

---

## What is Simulation-Only

These components exist only in the simulation environment and are NOT needed on the real robot:

| Component | Purpose | Why Simulation-Only |
|-----------|---------|---------------------|
| **Gazebo** (`ros_gz_sim`) | Physics/rendering engine | Real robot has physical hardware |
| **ros_gz_bridge** | Bridge ROS2 ↔ Gazebo messages | No Gazebo topics on real robot |
| `spawn_entity` | Place robot model in Gazebo world | Robot physically exists |
| `scan_frame_fixer.py` | Fix Gazebo frame_id naming (`scout_mini/base_link/...` prefix) | Real LiDAR publishes correct frame_ids directly |
| `imu_odom_corrector.py` | Fuse IMU gyro into Gazebo DiffDrive odometry | Real robot odometry comes from wheel encoders + IMU via `scout_base` driver |
| `odom_to_tf.py` | Publish `odom → base_link` TF from Gazebo odometry | Real `scout_base` driver publishes odom TF directly |
| `laser_merger.py` | Merge front+rear scans into `/merged/scan` | Real robot uses single front LiDAR initially; merger can be added later if needed |
| Gazebo world file | `.world` SDF file with walls/obstacles | Physical environment replaces simulated world |
| `robot_state_publisher` (in Gazebo launch) | Counterpart; can be reused but with different params | Needed on real robot but with `use_sim_time:=false` |
| `use_sim_time: True` | Simulation clock synchronization | Real robot uses system wall clock |

---

## What Can Be Reused on Physical Scout Mini

These components are exactly the same in both simulation and real robot:

| Component | Notes |
|-----------|-------|
| **Nav2 core nodes** (`planner_server`, `controller_server`, `bt_navigator`, `recoveries_server`, `waypoint_follower`, `lifecycle_manager`) | Identical — only `use_sim_time` and scan topic differ |
| **AMCL** (`nav2_amcl`) | Same algorithm; scan topic must point to real LiDAR topic |
| **map_server** | Same map file can be used (if map matches real environment); must create new map via SLAM for real space |
| **Behavior tree XML** (`navigate_no_init_check.xml`) | Reused directly |
| **DWB controller parameters** (critics, tolerances) | Reused with conservative velocity limits for first test |
| **RViz2 configuration** | Same visualization tool, use `use_sim_time:=false` |
| **`send_nav2_goals.py`** | Goal-sending script works identically against real Nav2 action server |

---

## What Must Change for the Real Robot

### 1. CAN Interface

| Aspect | Simulation | Real Robot |
|--------|-----------|------------|
| **Bus** | None (Gazebo DiffDrive plugin) | CAN bus (typically `can0`) |
| **Driver** | `ros_gz_bridge` forwards `/cmd_vel` | `scout_base` node communicates over CAN to motor controllers |
| **Setup** | N/A | `sudo ip link set can0 up type can bitrate 500000` |
| **Launch** | N/A | `ros2 launch scout_base scout_mini_base.launch.py` |

The `scout_base` package must be running on the real robot's onboard computer to publish `/odom`, `/joint_states`, and subscribe to `/cmd_vel`.

### 2. LiDAR Ethernet Setup

| Aspect | Simulation | Real Robot |
|--------|-----------|------------|
| **Connection** | Gazebo ray sensor plugin | Ethernet (RS-AIRY LiDAR connects via RJ45) |
| **IP** | N/A | Typically `192.168.1.x` for the LiDAR |
| **Driver** | N/A | `ros2 run urg_node urg_node_driver` or vendor-specific ROS 2 driver |
| **Topic** | `/front/scan` (via `ros_gz_bridge`) | `/front/scan` (from real LiDAR driver) |
| **Frame ID** | `scout_mini/base_link/front_lidar_sensor` (needs fixer) | `front_lidar_link` (correct directly from driver) |

Verify that the LiDAR driver publishes to `/front/scan` with `frame_id: front_lidar_link`.

### 3. Emergency Stop

| Aspect | Simulation | Real Robot |
|--------|-----------|------------|
| **E-stop** | `Ctrl+C` in terminal | Physical emergency stop button on Scout Mini |
| **Software stop** | Stop `/cmd_vel` publishing | Stop `/cmd_vel` OR press physical E-stop |
| **Test protocol** | N/A | Keep E-stop within reach during all autonomous tests |

Always test E-stop functionality before running autonomous navigation. Verify that stopping `/cmd_vel` (or pressing physical E-stop) immediately halts the robot.

### 4. Low-Speed First Test

For the first real-world test, use **conservative velocity limits** (already configured in `config/real_robot/nav2_params.yaml`):

| Parameter | Simulation | Real Robot (First Test) |
|-----------|-----------|--------------------------|
| `max_vel_x` | 0.5 m/s | **0.3 m/s** |
| `max_vel_theta` | 1.0 rad/s | **0.5 rad/s** |
| `acc_lim_x` | 1.0 m/s² | **0.5 m/s²** |
| `acc_lim_theta` | 2.0 rad/s² | **1.0 rad/s²** |
| `xy_goal_tolerance` | 0.25 m | **0.3 m** |

After confirming safe operation, these can be gradually increased.

### 5. Obstacle-Free Initial Test

**First test protocol:**
1. Clear the test area of all obstacles and personnel.
2. Start with a simple straight-line goal ~1 meter ahead.
3. Verify the robot moves forward and stops at the goal.
4. Test a single turn (e.g., 90° rotation in place).
5. Gradually increase complexity — add one obstacle at a time.
6. Only after successful obstacle-free tests, test with obstacles present.

This incremental approach isolates configuration issues from environmental variables.

### 6. Sensor Coordinate Frame Verification

Before running navigation, verify the TF tree matches the physical robot:

```bash
# Check TF tree
ros2 run tf2_tools view_frames

# Verify LiDAR frame
ros2 run tf2_ros tf2_echo base_link front_lidar_link

# Verify odometry frame
ros2 run tf2_ros tf2_echo odom base_link

# Verify scan data has correct frame_id
ros2 topic echo /front/scan --once | grep frame_id
```

Expected TF chain: `map → odom → base_link → front_lidar_link`

If frame_ids don't match, update the LiDAR driver or add a static transform publisher.

---

## Summary

| Layer | Simulation | Real Robot |
|-------|-----------|------------|
| **Physics** | Gazebo Ignition | Physical Scout Mini |
| **Robot driver** | `ros_gz_bridge` + DiffDrive plugin | `scout_base` over CAN |
| **LiDAR** | Gazebo ray sensor → `ros_gz_bridge` | Ethernet LiDAR → vendor driver |
| **Odometry** | Gazebo DiffDrive → `imu_odom_corrector` → `odom_to_tf` | `scout_base` publishes `/odom` directly |
| **Sensor processing** | `scan_frame_fixer`, `laser_merger` | None needed (real frame_ids are correct) |
| **Time** | `use_sim_time: True` | `use_sim_time: False` |
| **Safety** | `Ctrl+C` | Physical E-stop + software stop |
| **Nav2 stack** | Same (planner, controller, AMCL, BT) | Same (planner, controller, AMCL, BT) |
| **Launch** | `nav2_simulation_launch.py` | `nav2_real_robot_launch.py` |
| **Params** | `config/simulation/nav2_params.yaml` | `config/real_robot/nav2_params.yaml` |

The Nav2 core is identical — only the sensor/driver layer and time source differ. This separation ensures clean, reproducible simulation tests while keeping the real robot configuration ready for physical deployment.
