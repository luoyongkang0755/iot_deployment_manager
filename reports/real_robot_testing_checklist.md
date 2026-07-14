# Real Robot Testing Checklist — Scout Mini Nav2 Deployment

> **WARNING**: This checklist must be completed in order before any autonomous navigation test on the physical Scout Mini. If any check fails, stop and resolve the issue before proceeding.

---

## Phase 1 — Safety & Hardware Setup

### 1.1 Emergency Stop Verification
- [ ] Confirm physical emergency stop button is accessible and functional
- [ ] Press E-stop and verify robot motors are **immediately disabled**
- [ ] Release E-stop and verify robot can be re-enabled
- [ ] Test software stop: publish zero `Twist` on `/cmd_vel` → robot halts

### 1.2 Battery Check
- [ ] Confirm battery voltage is within normal range (Scout Mini: ~24V nominal)
- [ ] Confirm battery is sufficiently charged (> 50%) for testing duration
- [ ] Check battery connections are secure, no loose cables

### 1.3 Robot Physical Preparation
- [ ] **Lift robot or ensure wheels are free-spinning** for first motor test
- [ ] Check all cables (CAN, Ethernet, power) are securely connected
- [ ] Clear test area of personnel and obstacles
- [ ] Ensure at least 3m × 3m clear space for initial tests

---

## Phase 2 — Communication & Driver Verification

### 2.1 CAN Interface
- [ ] Confirm CAN interface name (typically `can0`): `ip link show`
- [ ] Bring up CAN interface: `sudo ip link set can0 up type can bitrate 500000`
- [ ] Verify CAN interface is UP: `ip link show can0 | grep UP`
- [ ] Launch Scout Mini base driver: `ros2 launch scout_base scout_mini_base.launch.py`
- [ ] Confirm driver publishes `/joint_states` and subscribes to `/cmd_vel`

### 2.2 Front LiDAR (RS-AIRY)
- [ ] Confirm front LiDAR IP address: ping `192.168.1.x`
- [ ] Launch front LiDAR driver (e.g., `urg_node` or vendor ROS 2 driver)
- [ ] Confirm LiDAR publishes on `/front/scan`
- [ ] Verify LiDAR frame_id is `front_lidar_link`: `ros2 topic echo /front/scan --once | grep frame_id`

### 2.3 Rear LiDAR (RS-AIRY) — if applicable
- [ ] Confirm rear LiDAR IP address: ping `192.168.1.y`
- [ ] Launch rear LiDAR driver
- [ ] Confirm LiDAR publishes on `/rear/scan`
- [ ] Verify LiDAR frame_id is `rear_lidar_link`

---

## Phase 3 — Validation Before Movement

### 3.1 TF Tree Verification
- [ ] Generate TF tree: `ros2 run tf2_tools view_frames`
- [ ] Confirm chain: `map → odom → base_link → front_lidar_link`
- [ ] Confirm chain: `map → odom → base_link → rear_lidar_link` (if installed)
- [ ] Verify transforms have correct translation values (check URDF)
- [ ] **STOP if any TF is missing or incorrect**

### 3.2 Odometry Verification
- [ ] Confirm `/odom` topic is publishing
- [ ] Check odometry frame_id is `odom`, child_frame_id is `base_link`
- [ ] Manually push robot forward and verify odometry values change correctly
- [ ] **STOP if odometry values are zero, inverted, or erratic**

### 3.3 LiDAR Data Verification
- [ ] Open RViz2 and add LaserScan display for `/front/scan`
- [ ] Confirm scan data matches physical environment (walls, objects visible)
- [ ] Move an object in front of LiDAR and confirm scan updates in real time
- [ ] Check scan frequency is stable (~10 Hz)
- [ ] **STOP if scan data is empty, out of range, or shows ghost patterns**

---

## Phase 4 — Low-Speed Motor Tests

> **Important**: Robot must be lifted or on a stand for the first motor test.

### 4.1 Manual cmd_vel Test (Robot Lifted)
- [ ] Publish slow forward: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}}" --once`
- [ ] Verify wheels spin forward
- [ ] Publish slow reverse: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -0.1}}" --once`
- [ ] Verify wheels spin reverse
- [ ] Publish stop: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{}" --once`
- [ ] Publish slow turn: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{angular: {z: 0.2}}" --once`
- [ ] Verify wheels turn in correct direction
- [ ] **STOP if wheels don't move, move in wrong direction, or make unusual noise**

### 4.2 Ground Contact Test
- [ ] Place robot on ground in open area (keep E-stop within reach)
- [ ] Publish very slow forward (0.05 m/s) for 1 second
- [ ] Confirm robot moves forward as expected
- [ ] Publish stop immediately after
- [ ] Repeat for reverse motion
- [ ] **STOP if robot does not move, moves erratically, or overruns**

---

## Phase 5 — Obstacle-Free Nav2 Test

### 5.1 Launch Nav2 Stack
- [ ] Ensure `use_sim_time` is `false`
- [ ] Load a map matching the test environment (run SLAM first if needed)
- [ ] Launch Nav2: `ros2 launch scout_mini_dual_lidar_gazebo nav2_real_robot_launch.py`
- [ ] Confirm all 7 Nav2 nodes are active + lifecycle_manager

### 5.2 Set Initial Pose
- [ ] In RViz2, use "2D Pose Estimate" to set robot's actual position on map
- [ ] Verify AMCL particle cloud converges to a single cluster
- [ ] Verify `/amcl_pose` is publishing

### 5.3 Simple Straight-Line Goal
- [ ] Send a goal **1 meter directly ahead** of the robot
- [ ] Keep hand on E-stop during the entire test
- [ ] Observe robot moves forward smoothly
- [ ] Confirm robot reaches goal and stops (no overshoot)
- [ ] **STOP if robot veers off course, oscillates, or fails to stop**

### 5.4 Turn-in-Place Goal
- [ ] Send a goal requiring a ~90° rotation
- [ ] Observe robot turns smoothly
- [ ] Confirm robot reaches goal orientation
- [ ] **STOP if robot overshoots, undershoots, or spins uncontrollably**

### 5.5 Multi-Point Navigation
- [ ] Send two sequential goals at safe distances
- [ ] Confirm robot navigates both successfully
- [ ] Monitor for any recovery behavior triggers

---

## Phase 6 — Post-Test Shutdown

- [ ] Stop all Nav2 nodes
- [ ] Stop LiDAR drivers
- [ ] Stop `scout_base` driver
- [ ] Bring down CAN interface: `sudo ip link set can0 down`
- [ ] Disconnect battery
- [ ] Document any issues in test log

---

## Stop Criteria

**Immediately stop the test and press E-stop if any of the following occur:**

- [ ] Odometry values are incorrect or inverted
- [ ] TF tree is missing transforms or has wrong values
- [ ] LiDAR data is empty, incorrect frame_id, or shows artifacts
- [ ] Robot does not respond to `/cmd_vel` commands
- [ ] Robot moves in unexpected direction
- [ ] Robot vibrates, makes unusual noise, or moves erratically
- [ ] Robot approaches a wall, person, or obstacle unexpectedly
- [ ] Any smoke, spark, or unusual smell from robot

---

## Test Log

| Date | Tester | Phase | Result | Notes |
|------|--------|-------|--------|-------|
| — | — | — | — | — |

---

## Summary

This checklist ensures a systematic, safety-first approach to real robot testing. Each phase must pass before proceeding to the next. The conservative velocity limits in [`config/real_robot/nav2_params.yaml`](../src/scout_mini_dual_lidar_gazebo/config/real_robot/nav2_params.yaml) provide an additional safety margin during initial tests.
