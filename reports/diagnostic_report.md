# Nav2 "Failed to transform from to map" Diagnostic Report

**Date:** 2026-07-10  
**Robot:** Scout Mini (simulated in Gazebo Ignition)  
**Issue:** `planner_server` fails to transform robot pose to map frame, reporting `Failed to transform from  to map` (empty `from` frame).

---

## 1. Environment & Context

- ROS 2 Humble + Gazebo Ignition (gz-sim)
- Two RS-AIRY LiDARs (front + rear), merged via `laser_merger.py` into `/merged/scan`
- DiffDrive odometry bridged via `ros_gz_bridge`, frame IDs corrected by `imu_odom_corrector.py` and `odom_to_tf.py`
- Nav2 nodes managed by `lifecycle_manager`

---

## 2. Diagnostic Commands & Results

### 2.1 Lifecycle State Check

All Nav2 nodes are `active [3]`:

```bash
$ for node in map_server amcl planner_server controller_server recoveries_server bt_navigator waypoint_follower; do
    echo -n "$node: "; ros2 lifecycle get /$node
  done

map_server: active [3]
amcl: active [3]
planner_server: active [3]
controller_server: active [3]
recoveries_server: active [3]
bt_navigator: active [3]
waypoint_follower: active [3]
```

**Result:** OK — all nodes active.

---

### 2.2 AMCL Scan Topic Subscription

```bash
$ ros2 node info /amcl | grep -i scan
    /merged/scan: sensor_msgs/msg/LaserScan
```

**Result:** OK — AMCL subscribes to `/merged/scan` correctly.

---

### 2.3 Merged Scan Data Integrity

```bash
$ ros2 topic echo /merged/scan --once | head -5
 header:
   stamp:
     sec: 915
     nanosec: 800000000
   frame_id: base_link
```

```bash
$ ros2 topic echo /merged/scan --once | grep -c "inf"
6
```

**Result:** OK — 354 valid points, only 6 `inf`. Laser data is healthy.

---

### 2.4 Raw Scan Frame ID Check

```bash
$ ros2 topic echo /front/scan --once | grep frame_id
   frame_id: scout_mini/base_link/front_lidar_sensor
```

**Finding:** The Gazebo `<ros><frame_id>` tag is **not effective** in this Gazebo version — the raw scan arrives with the `scout_mini/` model name prefix in the frame_id. A `scan_frame_fixer.py` node was created to remap:

```
/front/scan (frame_id: scout_mini/base_link/front_lidar_sensor)
    → /front/scan_fixed (frame_id: front_lidar_link)
/rear/scan  (frame_id: scout_mini/base_link/rear_lidar_sensor)
    → /rear/scan_fixed  (frame_id: rear_lidar_link)
```

`laser_merger.py` then reads `/front/scan_fixed` + `/rear/scan_fixed` and publishes `/merged/scan` with `frame_id: base_link`.

---

### 2.5 TF Tree: odom → base_link

```bash
$ ros2 run tf2_ros tf2_echo odom base_link -r 0.5
 At time 946.300000000
 - Translation: [0.154, -0.150, 0.000]
 - Rotation: in RPY (degree) [0.000, -0.000, -178.921]
```

**Result:** OK — `odom → base_link` TF exists and is published consistently.

---

### 2.6 TF Tree: map → base_link

```bash
$ ros2 run tf2_ros tf2_echo map base_link 2>&1 | head -15
[INFO] Waiting for transform map -> base_link:
  Invalid frame ID "map" passed to canTransform argument target_frame
  - frame does not exist

[INFO] Waiting for transform map -> base_link:
  Lookup would require extrapolation into the past.
  Requested time 2133.170000 but the earliest data is at time 2133.200000
```

**Finding:**
1. The `map` frame **does exist** (AMCL is publishing `map → odom`), but the first lookup fails because `tf2_echo` starts before AMCL publishes the first transform.
2. **Critical:** `extrapolation into the past` — the TF timestamp (2133.200) is later than the requested timestamp (2133.170). This means `planner_server`'s default `transform_tolerance` (~0.1s) is **too small** for the ~0.03s offset between the laser scan timestamp and the latest TF data.

---

### 2.7 Odom Frame ID Correction

```bash
$ ros2 topic echo /odom_raw --once | grep frame_id
   frame_id: scout_mini/odom            # Raw DiffDrive with prefix

$ ros2 topic echo /odom --once | grep frame_id
   frame_id: odom                       # Corrected by imu_odom_corrector
   child_frame_id: base_link
```

**Result:** OK — `imu_odom_corrector.py` successfully strips the `scout_mini/` prefix from odom frame IDs.

---

### 2.8 Nav2 Goal Test (Command Line)

```bash
$ ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, ... }}, behavior_tree: ''}"

Goal accepted with ID: ...
Goal finished with status: ABORTED
```

**Result:** Even with `frame_id: 'map'` explicitly set in the goal, the planner still fails — confirming the issue is **server-side**, not RViz.

---

## 3. Root Cause Analysis

The error `Failed to transform from  to map` (empty `from` frame) is triggered when `planner_server` cannot look up the robot's pose in the `map` frame. This can happen when:

1. **TF timestamp mismatch:** The laser scan timestamp (used to derive the robot pose) is ~0.03s behind the latest TF data, exceeding the default `transform_tolerance` of 0.1s.
2. **Missing `transform_tolerance` in planner_server config:** `planner_server` did not have `transform_tolerance` configured, so it uses a very small default.
3. **TF extrapolation:** `odom_to_tf.py` was using `msg.header.stamp` (slightly old) rather than `self.get_clock().now()` for the TF timestamp, causing TF queries that requested the scan timestamp to fail with "extrapolation into the past".

---

## 4. Fixes Applied

### 4.1 `planner_server` — add `transform_tolerance`

```yaml
planner_server:
  ros__parameters:
    transform_tolerance: 1.0   # was: not set (default ~0.1)
```

### 4.2 `controller_server` — add `transform_tolerance`

```yaml
controller_server:
  ros__parameters:
    transform_tolerance: 1.0   # was: not set (default ~0.1)
```

### 4.3 `FollowPath` (DWB) — increase `transform_tolerance`

```yaml
FollowPath:
  plugin: "dwb_core::DWBLocalPlanner"
  transform_tolerance: 1.0     # was: 0.2
```

### 4.4 `local_costmap` — add `transform_tolerance`

```yaml
local_costmap:
  local_costmap:
    ros__parameters:
      transform_tolerance: 1.0   # was: not set
```

### 4.5 `global_costmap` — add `transform_tolerance`

```yaml
global_costmap:
  global_costmap:
    ros__parameters:
      transform_tolerance: 1.0   # was: not set
```

### 4.6 `odom_to_tf.py` — use current time for TF stamp

```python
# Before:
t.header.stamp = msg.header.stamp

# After:
t.header.stamp = self.get_clock().now().to_msg()
```

This prevents "extrapolation into the past" errors when other nodes query the `odom → base_link` TF at the laser scan timestamp.

---

## 5. Files Modified

| File | Change |
|---|---|
| `config/nav2_params.yaml` | Added `transform_tolerance: 1.0` to planner_server, controller_server, local_costmap, global_costmap, and DWB FollowPath |
| `src/odom_to_tf.py` | Changed TF timestamp from `msg.header.stamp` to `self.get_clock().now()` |
| `src/laser_merger.py` | Reduced hull filter from `0.35` to `0.08` (was over-filtering valid points) |
| `src/imu_odom_corrector.py` | Changed from IMU gyro integration (drift) to DiffDrive pose pass-through |
| `src/scan_frame_fixer.py` | **New file** — remaps LiDAR frame_id from `scout_mini/...` to URDF link names |
| `urdf/scout_mini.gazebo` | Added `<ros><frame_id>` tags to LiDAR and IMU sensors |
| `launch/scout_mini_gazebo.launch.py` | Added `scan_frame_fixer` node, removed redundant static TFs |

---

## 6. Current Status

- `/merged/scan` has valid data (354 points, 6 inf)
- AMCL is active and subscribed to `/merged/scan`
- `odom → base_link` TF chain is healthy
- `map → odom` TF is published by AMCL after initial pose is set
- **Issue persists:** `planner_server` still reports `Failed to transform from  to map`
