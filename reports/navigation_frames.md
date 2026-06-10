# Nav2 Coordinate Frame Chain Explanation Report

## Overview

This report explains the coordinate frame chain and their interrelationships used in the Nav2 navigation system, specifically for the Scout Mini dual-lidar robot.

---

## Coordinate Frame Chain Structure

### Complete Coordinate Frame Chain

```
map → odom → base_link → [front_lidar_link, rear_lidar_link]
```

### Coordinate Frame Hierarchy Diagram

```
map (World Coordinate Frame)
  └── odom (Odometry Coordinate Frame)
        └── base_link (Robot Base Coordinate Frame)
              ├── base_footprint (Ground Projection Coordinate Frame)
              ├── front_lidar_link (Front LiDAR Coordinate Frame)
              ├── rear_lidar_link (Rear LiDAR Coordinate Frame)
              ├── front_left_wheel_link (Front Left Wheel Coordinate Frame)
              ├── front_right_wheel_link (Front Right Wheel Coordinate Frame)
              ├── rear_left_wheel_link (Rear Left Wheel Coordinate Frame)
              ├── rear_right_wheel_link (Rear Right Wheel Coordinate Frame)
              └── inertial_link (Inertial Coordinate Frame)
```

---

## Detailed Explanation of Each Coordinate Frame

### 1. map Coordinate Frame (World Coordinate Frame)

**Definition:**
- A globally fixed world coordinate frame
- Used for long-term navigation and global path planning
- Typically aligned with the map origin

**Characteristics:**
- Fixed in place (relative to the world)
- Maintained by SLAM or the map server
- Allows drift (accumulates errors over time)

**Usage:**
- Global path planning
- Map localization
- Long-term task execution

**In RViz2:**
- When the Fixed Frame is set to `map`, you can see the robot's global position within the map
- Map data is typically published in the map coordinate frame

---

### 2. odom Coordinate Frame (Odometry Coordinate Frame)

**Definition:**
- A local coordinate frame whose origin is the robot's starting position
- Calculated via wheel odometry or visual odometry
- Accurate in the short term, but drifts over time

**Characteristics:**
- Relative to the robot's starting position
- High short-term precision (centimeter-level)
- Accumulates errors over time (drift)
- Continuous but may drift

**Usage:**
- Local path tracking
- Short-term obstacle avoidance
- Precise local motion control

**Relationship with map:**
- The `map → odom` transform is calculated by the localization system (e.g., AMCL)
- This transform is adjusted over time to correct for odometry drift

---

### 3. base_link Coordinate Frame (Robot Base Coordinate Frame)

**Definition:**
- A coordinate frame fixed to the robot's body
- Typically located at the robot's geometric center or rotation center
- All sensors and actuators are referenced relative to this frame

**Characteristics:**
- Moves with the robot
- Serves as the robot's "body" coordinate frame
- The parent frame for all sensor coordinate frames

**Usage:**
- Sensor data fusion
- Motion control
- Reference point for coordinate transformations

**On the Scout Mini:**
- Located at the robot's center
- Height is 0.145m above the ground (wheel radius)

---

### 4. base_footprint Coordinate Frame (Ground Projection Coordinate Frame)

**Definition:**
- The vertical projection of base_link onto the ground
- Same X and Y position as base_link, but Z=0 (ground level)

**Characteristics:**
- Reference point for 2D navigation
- Used for planar mobile robots

**Usage:**
- 2D path planning
- Costmap calculation

---

### 5. LiDAR Coordinate Frames

#### Front LiDAR Coordinate Frame

**Frame Names:**
- In URDF: `front_lidar_link`
- In Gazebo: `scout_mini/base_link/front_lidar_sensor`
- Connected via static TF transform

**Position:**
- Relative to base_link: (x=0.245, y=0, z=0.14)
- Located at the front center of the robot

**Usage:**
- Front obstacle detection
- Forward SLAM mapping
- Forward path planning

#### Rear LiDAR Coordinate Frame

**Frame Names:**
- In URDF: `rear_lidar_link`
- In Gazebo: `scout_mini/base_link/rear_lidar_sensor`
- Connected via static TF transform

**Position:**
- Relative to base_link: (x=-0.245, y=0, z=0.14)
- Located at the rear center of the robot

**Usage:**
- Rear obstacle detection
- Backward SLAM mapping
- 360° environment perception

---

## Detailed Coordinate Frame Transforms

### map → odom Transform

**Publisher:** AMCL or SLAM node

**Characteristics:**
- Adjusted over time
- Corrects odometry drift
- Discontinuous (may jump)

**Calculation:**
```
T_map_odom = T_map_robot_actual × T_odom_robot_odom^-1
```

### odom → base_link Transform

**Publisher:** robot_state_publisher

**Characteristics:**
- Continuous and smooth
- Derived from odometry data
- Accumulates errors

**Data Sources:**
- Wheel odometry
- Visual odometry
- IMU data fusion

### base_link → LiDAR Transform

**Publisher:** Static TF publisher node

**Characteristics:**
- Fixed and unchanging
- Derived from the URDF model
- Precisely known

**Transform Values:**
```python
# Front LiDAR
base_link → front_lidar_link: (0.245, 0, 0.14, 0, 0, 0)

# Rear LiDAR
base_link → rear_lidar_link: (-0.245, 0, 0.14, 3.14159, 0, 0)
```

---

## Key Differences Comparison

### map vs odom

| Feature | map | odom |
|---------|-----|------|
| **Origin** | World-fixed point | Robot starting position |
| **Stability** | Globally fixed | Moves with the robot |
| **Accuracy** | Accurate long-term | Accurate short-term, drifts long-term |
| **Continuity** | May jump | Continuous and smooth |
| **Usage** | Global planning | Local control |
| **Transform Calculation** | AMCL/SLAM | Odometry |

### base_link vs LiDAR Coordinate Frames

| Feature | base_link | LiDAR Coordinate Frame |
|---------|-----------|------------------------|
| **Definition** | Robot body | Sensor mounting location |
| **Motion** | Moves with the robot | Moves with the robot |
| **Transform** | Reference frame | Fixed relative to base_link |
| **Data** | Robot state | Laser scan data |

---

## TF Tree Verification

### View the TF Tree

```bash
ros2 run tf2_tools view_frames
```

The generated `frames.pdf` should display the complete coordinate frame chain.

### Check Specific Transforms

```bash
# Check map → base_link transform
ros2 run tf2_ros tf2_echo map base_link

# Check odom → base_link transform
ros2 run tf2_ros tf2_echo odom base_link

# Check base_link → front_lidar_link transform
ros2 run tf2_ros tf2_echo base_link front_lidar_link
```

### Verify Coordinate Frame Chain Integrity

```bash
# The following transforms should be queryable successfully
ros2 run tf2_ros tf2_echo map front_lidar_link
ros2 run tf2_ros tf2_echo map rear_lidar_link
```

---

## Common Issues

### Issue 1: Broken Coordinate Frame Chain

**Symptoms:** Unable to display lidar data or map in RViz

**Check:**
```bash
ros2 run tf2_tools view_frames
```

**Solution:** Ensure all static TF transforms are properly configured

### Issue 2: Mismatch Between map and odom

**Symptoms:** The robot's position in the map does not match reality

**Cause:** Inaccurate AMCL localization or incorrect initial position

**Solution:** Re-initialize the robot position or adjust AMCL parameters

### Issue 3: Incorrect LiDAR Data Coordinate Frame

**Symptoms:** Laser point cloud appears in the wrong location

**Cause:** Incorrect TF transform parameters or frame_id mismatch

**Solution:** Check the static TF transform values and the laser data's frame_id

---

## Acceptance Checklist

- ✅ No disconnected coordinate frames
- ✅ All coordinate frames are correctly connected to the TF tree
- ✅ The difference between map and odom has been clearly explained
- ✅ The relationship between base_link and LiDAR coordinate frames has been clarified
- ✅ TF tree image has been generated (`frames.pdf`)

---

## Submitted Files

- `reports/navigation_frames.md` (this report)
- `media/screenshots/task18_tf_tree.pdf` (TF tree image)
- `TASK_LOG.md` (updated)
- `TASK_LOG_CHINESE.md` (updated)

---

## Date

2026-06-10
```
