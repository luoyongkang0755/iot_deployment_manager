# SLAM Pose Not Updating — Ghosting Artifacts

## Status
UNRESOLVED — pending verification after attempted fixes

## Symptom

Laser scanners work continuously and SLAM publishes maps, but the robot pose never updates. All scan frames are incorrectly stacked at the same origin position, creating repeated "ghost" obstacle rings in the map.

## Diagnosis

- TF tree structure is correct: `odom → scout_mini/odom → scout_mini/base_link → base_link`
- Dynamic transform `scout_mini/odom → scout_mini/base_link` updates at 50Hz with changing timestamps
- `/odom` topic has valid odometry data
- `/tf` topic has DiffDrive-published dynamic transforms

## Attempted Fixes

1. **Added timeouts to SLAM config** — `transform_timeout: 0.5` and `transform_tolerance: 0.1` in `slam_toolbox_params.yaml` to handle timing race conditions when looking up transforms at scan timestamps.
2. **Created `/tf_static → /tf` relay** — New `tf_static_relay.py` node forwards all `/tf_static` messages to `/tf`, consolidating transforms onto a single channel.

## Hypothesized Root Cause

`robot_state_publisher` publishes static transforms (URDF fixed joints: `base_link → base_footprint`, `base_link → front_lidar_link`, etc.) to `/tf_static`, while Gazebo DiffDrive publishes dynamic transforms (`scout_mini/odom → scout_mini/base_link`) to `/tf`. slam_toolbox in synchronous mode looks up `odom → base_link` at scan timestamps. If it cannot properly merge transforms from two separate TF channels, it may fail to assemble the full chain and treat the robot as stationary.

## Next Steps

- Rebuild and restart simulation after fixes
- Verify the relay node is forwarding `/tf_static` messages to `/tf`
- Check slam_toolbox logs for any TF-related warnings or errors
- If still unresolved, consider configuring slam_toolbox to subscribe to both `/tf` and `/tf_static` explicitly
