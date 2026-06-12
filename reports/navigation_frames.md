# Nav2 Coordinate Frame Chain Explanation Report

## Overview

This report explains the coordinate frame chain and their interrelationships used in the Nav2 navigation system, specifically for the Scout Mini dual-lidar robot. Updates in Task 18 reflect the actual TF tree after resolving the Gazebo model name prefix issue.

---

## Actual TF Tree Structure (Task 18 Verification)

The TF tree was verified via `ros2 run tf2_tools view_frames`. The actual chain includes **model prefix bridge frames** inserted between Gazebo's name-scoped frames and ROS standard frames:

```
Map      SLAM publishes       map → odom
Localization                 (updated by AMCL or SLAM Toolbox)

Prefix   Static identity TF   odom → scout_mini/odom
Bridge    (added in Task 17)  scout_mini/base_link → base_link

Gazebo   Diff drive plugin    scout_mini/odom → scout_mini/base_link
Odometry  (with "scout_mini/" prefix)

URDF     robot_state_publisher base_link → [front_lidar_link, rear_lidar_link,
Static                          base_footprint, inertial_link,
Transforms                      front_left_wheel_link, ...]
```

### Complete Coordinate Frame Chain

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → front_lidar_link
        ↓                              ↑
  (diff drive plugin publishes)  (static TF identity bridge)
```

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → rear_lidar_link
```

### Why the prefix bridge is needed

Ignition Gazebo diff drive plugin automatically prepends the model name (`scout_mini/`) to all frame IDs it publishes. This creates two disconnected TF sub-trees:

- **Sub-tree A** (from Gazebo bridge): `scout_mini/odom → scout_mini/base_link` (50 Hz)
- **Sub-tree B** (from robot_state_publisher): `base_link → front_lidar_link, rear_lidar_link, ...`

Without the bridge, SLAM Toolbox cannot find `odom → base_link` because `odom` and `base_link` (without prefix) are in different sub-trees — the TF chain is broken.

**Solution** (implemented in [scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py)):

```python
# Connect standard ROS odom to Gazebo's scout_mini/odom (identity)
static_transform_publisher 0 0 0 0 0 0 odom scout_mini/odom

# Connect Gazebo's scout_mini/base_link to ROS's base_link (identity)
static_transform_publisher 0 0 0 0 0 0 scout_mini/base_link base_link
```

### Coordinate Frame Hierarchy Diagram (Actual)

```
map                          (SLAM / AMCL)
  └── odom                   (ROS standard: identity bridge target)
        └── scout_mini/odom  (Gazebo odom frame with model prefix)
              └── scout_mini/base_link  (Gazebo base frame with model prefix)
                    └── base_link       (ROS standard: identity bridge source)
                          ├── base_footprint          (Ground projection)
                          ├── front_lidar_link        (Front RS-AIRY LiDAR)
                          ├── rear_lidar_link         (Rear RS-AIRY LiDAR)
                          ├── front_left_wheel_link   (Front left wheel)
                          ├── front_right_wheel_link  (Front right wheel)
                          ├── rear_left_wheel_link    (Rear left wheel)
                          ├── rear_right_wheel_link   (Rear right wheel)
                          └── inertial_link           (IMU / inertial)
```

**Gazebo Sensor Frames** (internal):
```
scout_mini/base_link/front_lidar_sensor  →  parent: front_lidar_link
scout_mini/base_link/rear_lidar_sensor   →  parent: rear_lidar_link
```
These are published by `robot_state_publisher` and only used by Gazebo sensors internally; not needed in RViz directly.

---

## Detailed Explanation of Each Coordinate Frame

### 1. map Coordinate Frame (World Coordinate Frame)

**Definition:**
- A globally fixed world coordinate frame aligned with the map origin
- Used for long-term navigation and global path planning

**Characteristics:**
- Fixed in place (relative to the world)
- Maintained by SLAM Toolbox (mapping mode) or AMCL (localization mode)
- Discontinuous — may jump when re-localized

**Publisher:** SLAM Toolbox node or AMCL node
**Transform Type:** Dynamic (updated periodically)

**Usage:**
- Global path planning (Nav2 PlannerServer)
- Map visualization in RViz
- Long-term task execution

**SLAM Toolbox Config** ([slam_toolbox_params.yaml](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/params/slam_toolbox_params.yaml#L15)):
```yaml
map_frame: map
```

---

### 2. odom Coordinate Frame (Odometry Coordinate Frame)

**Definition:**
- A local coordinate frame whose origin is the robot's starting position
- Represents the robot's motion as estimated by wheel odometry
- Accurate short-term but drifts long-term due to integration errors

**Characteristics:**
- Continuous and smooth — no jumps
- High short-term precision (centimeter-level)
- Accumulates unbounded drift over time

**Publisher:** Diff drive plugin in Gazebo (via `ros_gz_bridge` to ROS)
**Transform Type:** Smooth, continuous updates at 50 Hz

**Diff Drive Plugin Config** ([scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L157)):
```xml
<odom_frame>odom</odom_frame>
<robot_base_frame>base_footprint</robot_base_frame>
<odom_publish_frequency>50</odom_publish_frequency>
```

**Usage:**
- Local path tracking (Nav2 ControllerServer)
- Short-term obstacle avoidance
- `map → odom` transform published by SLAM/AMCL to correct drift

---

### 3. scout_mini/odom and scout_mini/base_link (Gazebo Prefix Frames)

**Background:**
Ignition Gazebo automatically prepends `{model_name}/` to all frame IDs published by model plugins. For our model named `scout_mini`, the diff drive plugin publishes:
- `scout_mini/odom → scout_mini/base_link`

**Bridge Frames** (identity transforms):
- `odom → scout_mini/odom` — bridges ROS standard to Gazebo-scoped frame
- `scout_mini/base_link → base_link` — bridges Gazebo-scoped to ROS standard frame

Both are **zero offset** (identity) transforms: translation = (0,0,0), rotation = (0,0,0).

**Publisher:** static_transform_publisher in launch file
**Transform Type:** Static (never changes)

These frames exist purely to connect the two naming conventions; they do not represent any physical offset.

---

### 4. base_link Coordinate Frame (Robot Base Coordinate Frame)

**Definition:**
- A coordinate frame fixed to the robot's body at its geometric center
- All sensors and URDF static transforms are relative to this frame

**Characteristics:**
- Moves with the robot
- Serves as the robot's "body" frame
- The parent for all sensor/wheel frames defined in URDF

**Position on Scout Mini:**
- Center of robot body (base_x_size/2 from front, base_y_size/2 from sides)
- Height: wheel_radius (0.145m) above ground (z-offset from base_footprint at ground level)

**Usage:**
- Sensor data fusion reference
- Motion control target
- URDF transform tree root

**SLAM Toolbox Config:**
```yaml
base_frame: base_link
```

---

### 5. base_footprint Coordinate Frame (Ground Projection)

**Definition:**
- The vertical projection of base_link onto the ground plane (z = -wheel_radius from base_link)
- Same X/Y position as base_link, Z = 0 at ground level

**URDF Definition** ([scout_mini.xacro](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/urdf/scout_mini.xacro#L52-L56)):
```xml
<joint name="base_footprint_joint" type="fixed">
    <origin xyz="0 0 ${-wheel_radius}" rpy="0 0 0" />
    <parent link="base_link" />
    <child link="base_footprint" />
</joint>
```
Where `wheel_radius = 0.145m`, so `base_footprint` is 0.145m below `base_link`.

**Usage:**
- 2D navigation and costmap reference point
- Used by Nav2's footprint model

---

### 6. LiDAR Coordinate Frames

#### Front LiDAR (RS-AIRY)

**Frame Name:** `front_lidar_link`

**Position Relative to base_link** ([scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L111)):
```xml
<origin xyz="${base_x_size/2 - 0.08} 0.0 ${base_z_size/2 + 0.05}" rpy="0 0 0" />
<!-- = (0.245, 0, 0.14) --!>
```
- 0.245m forward from center
- 0.14m above base_link center

**Sensor topic:** `/front/scan` (published at 5 Hz)
**360°** horizontal scan (samples=360, resolution=1°)

#### Rear LiDAR (RS-AIRY)

**Frame Name:** `rear_lidar_link`

**Position Relative to base_link** ([scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L141)):
```xml
<origin xyz="${-base_x_size/2 + 0.08} 0.0 ${base_z_size/2 + 0.05}" rpy="0 0 3.14159" />
<!-- = (-0.245, 0, 0.14) with 180° yaw rotation --!>
```
- 0.245m backward from center
- 0.14m above base_link center
- 180° yaw rotation (facing rear)

**Sensor topic:** `/rear/scan` (published at 5 Hz)
**360°** horizontal scan

---

## Key Differences Comparison

### map vs odom

| Feature | map | odom |
|---------|-----|------|
| **Origin** | World-fixed point (map origin) | Robot's starting position |
| **Stability** | Globally fixed, may jump | Moves with robot, always smooth |
| **Accuracy** | Long-term accurate (with loop closure) | Short-term accurate, drifts unbounded |
| **Continuity** | Discontinuous (jumps on re-localization) | Continuous and smooth |
| **Publisher** | SLAM Toolbox / AMCL | Gazebo diff drive → ros_gz_bridge |
| **Update Rate** | ~2–10 Hz (SLAM-dependent) | 50 Hz (odom_publish_frequency) |
| **Usage** | Global path planning, map-based tasks | Local motion control, obstacle avoidance |
| **Error Accumulation** | Bounded by loop closure / map matching | Unbounded drift accumulation |

**Why both are needed:**
- `odom` provides smooth, high-frequency state for real-time control
- `map` provides global positioning corrected against known landmarks
- `map → odom` transform bridges the drift: as SLAM corrects global position, it adjusts the `map → odom` offset so that the robot's latest `odom → base_link` still points to the correct `map` position

### base_link vs LiDAR Frames

| Feature | base_link | front_lidar_link | rear_lidar_link |
|---------|-----------|-----------------|-----------------|
| **Position (relative to base_link)** | — | (0.245, 0, 0.14) | (-0.245, 0, 0.14) |
| **Orientation** | Forward (0°) | Forward (0°) | Rear-facing (180°) |
| **Data Published** | Robot pose (from odom) | /front/scan | /rear/scan |
| **Transform Type** | Reference frame | Static (URDF) | Static (URDF) |
| **Used By** | Nav2 planners, controllers | SLAM (primary scan) | Obstacle detection (if merged) |

---

## Coordinate Frame Transform Details

### map → odom (Localization Correction)

**Publisher:** SLAM Toolbox (mapping mode) or AMCL (localization mode)

**Behavior:**
- Updated whenever SLAM/AMCL refines the robot's global position
- Can "jump" discretely (the transform value changes step-wise)
- During initial mapping: SLAM Toolbox sets `map = odom` at the origin, then updates as it builds the map

**Check:**
```bash
ros2 run tf2_ros tf2_echo map odom
```

### odom → base_link (Odometry Motion)

**Publisher:** Gazebo diff drive plugin → ros_gz_bridge → /tf topic

**Behavior:**
- Continuous, smooth updates at 50 Hz
- Derived from wheel encoder simulation in Gazebo
- More accurate near the start, increasingly drifts over long runs

**Bridge Config** ([scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py)):
```
/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V
```

### base_link → LiDAR (Static URDF Transforms)

**Publisher:** robot_state_publisher

**Behavior:**
- Permanent, never-changing transforms
- Defined by the URDF model's `<joint>` elements
- Both LiDARs are fixed to the robot body (no moving joints)

**Check:**
```bash
ros2 run tf2_ros tf2_echo base_link front_lidar_link
ros2 run tf2_ros tf2_echo base_link rear_lidar_link
```

---

## TF Tree Verification Commands

### View the complete TF tree
```bash
ros2 run tf2_tools view_frames
```
The generated `frames.pdf` displays all connected coordinate frames.

### Check specific transforms
```bash
# Localization chain (drift correction)
ros2 run tf2_ros tf2_echo map odom

# Odometry chain (high-frequency motion)
ros2 run tf2_ros tf2_echo odom base_link

# LiDAR transforms (static, URDF-defined)
ros2 run tf2_ros tf2_echo base_link front_lidar_link
ros2 run tf2_ros tf2_echo base_link rear_lidar_link
```

### Verify end-to-end chain integrity
```bash
ros2 run tf2_ros tf2_echo map front_lidar_link     # Should succeed
ros2 run tf2_ros tf2_echo map rear_lidar_link      # Should succeed
ros2 run tf2_ros tf2_echo odom front_lidar_link    # Should succeed
```

### Check Gazebo internal frames (if debugging)
```bash
ign topic -l | grep tf     # List Gazebo TF-related topics
ign topic -i -t /tf        # Show Gazebo /tf message type
```

---

## Common Issues and Solutions

### Issue 1: Broken Coordinate Frame Chain

**Symptoms:** 
- RViz cannot display LaserScan or Map
- `ros2 topic echo /map --once` returns nothing
- `ros2 run tf2_ros tf2_echo map base_link` fails

**Root Cause (this project):**
Gazebo diff drive plugin publishes `scout_mini/odom → scout_mini/base_link` (model name prefix), while `robot_state_publisher` uses `base_link` (no prefix). Two unconnected TF sub-trees.

**Solution:**
Add static identity TF transforms: `odom → scout_mini/odom` and `scout_mini/base_link → base_link`.

**Check:**
```bash
ros2 run tf2_tools view_frames
# Must show a single connected tree from map to all leaf frames
```

### Issue 2: map and odom Mismatch

**Symptoms:** Robot appears at the wrong position on the map in RViz.

**Cause:** AMCL localization not accurate, or SLAM has not yet established `map → odom`.

**Solution:** 
- During mapping: ensure `mode: mapping` and drive the robot in loops for loop closure.
- During localization: provide a good initial pose estimate via RViz's "2D Pose Estimate" tool.

### Issue 3: Incorrect LiDAR Data Positioning

**Symptoms:** Laser point cloud appears offset from the robot model in RViz.

**Cause:** The `front_lidar_link` or `rear_lidar_link` static transforms have wrong values.

**Check URDF joint positions:**
```bash
ros2 run tf2_ros tf2_echo base_link front_lidar_link
# Should report translation: (0.245, 0, 0.14)
```

---

## Acceptance Checklist

- ✅ No disconnected coordinate frames — all frames connected in a single TF tree
- ✅ `map → odom` difference clearly explained (discrete vs continuous)
- ✅ `base_link` vs LiDAR frame relationship explained (static transforms from URDF)
- ✅ Model prefix bridging mechanism documented
- ✅ TF tree image generated via `ros2 run tf2_tools view_frames`
- ✅ All end-to-end transforms verifiable (`map → front_lidar_link` works)

---

## Submitted Files

- `reports/navigation_frames.md` (this report, updated for Task 18)
- `reports/frames_chinese.md` (Chinese version, updated for Task 18)
- `TASK_LOG.md` (updated)
- `TASK_LOG_CHINESE.md` (updated)

---

## Date

2026-06-12 (Task 18 — updated with actual TF tree from verified Gazebo + SLAM pipeline)
