# Scout Mini Dual LiDAR Simulation Troubleshooting Log

## Problem Description

When using Nav2 navigation, the ROS side could not receive LiDAR data, and both `ros2 topic echo /front/scan` and `ign topic -e -t /front/scan` had no data output.

## Troubleshooting Process

### Phase 1: Basic Configuration Check

#### 1. QoS Configuration Issue
**Problem**: Gazebo uses BestEffort QoS while ROS defaults to Reliable QoS, causing data transmission failure.

**Attempted Solution**:
- Added `qos_sensor_data: True` parameter to ros_gz_bridge in launch file
- Tried using `--ros-args` to pass QoS parameters (failed, incorrect parameter passing method)

**Result**: QoS configuration consistent, but problem not resolved.

#### 2. Environment Variable Setting Order Issue
**Problem**: `GZ_SIM_RESOURCE_PATH` was set after Gazebo starts, causing Gazebo to fail to find model resources.

**Solution**: Moved environment variable settings before Gazebo starts.

**Modified Location**: `scout_mini_gazebo.launch.py`

**Result**: Gazebo successfully loads model files after fix.

#### 3. World File Missing Sensor System
**Problem**: World file missing `sensors-system` plugin, causing sensors to fail to initialize.

**Solution**: Added to `<world name="simple_test_world">` tag in world file:
```xml
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
    <rendering>true</rendering>
    <sensor_update_rate>10</sensor_update_rate>
</plugin>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"></plugin>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"></plugin>
```

**Result**: Sensor system successfully loaded, `/front/scan` and `/rear/scan` topics visible with `ign topic -l`.

#### 4. Gazebo Resource Path Configuration Error
**Problem**: Resource path setting incorrect, Gazebo could not find `model://scout_description/meshes/base_link.dae`.

**Incorrect Configuration**:
```python
gz_resource_path = pkg_scout_description + '/meshes:' + pkg_scout_gazebo + '/worlds'
# Result: /ws/install/scout_description/share/scout_description/meshes (wrong)
```

**Correct Configuration**:
```python
scout_description_parent = os.path.dirname(pkg_scout_description)
gz_resource_path = scout_description_parent + ':' + pkg_scout_gazebo + '/worlds'
# Result: /ws/install/scout_description/share (correct)
```

**Result**: Gazebo correctly loads 3D model files, robot model and colored obstacles visible in GUI.

#### 5. Python Import Error
**Problem**: Importing `os` module inside function causes `UnboundLocalError`.

**Solution**: Import `import os` at the top of the file.

**Result**: Launch file loads normally.

#### 6. Adding Obstacles for Testing
**Problem**: Robot surrounded by empty space, cannot verify if sensor is working properly.

**Solution**: Added 4 obstacle boxes in world file:
- obstacle_box_1: Front 2.0m
- obstacle_box_2: Left 2.0m
- obstacle_box_3: Right 2.0m
- obstacle_box_4: Back 2.0m

**Result**: Colored boxes visible in Gazebo GUI, but sensor still has no data.

### Phase 2: Deep Diagnostics

#### 7. Gazebo Version Compatibility Check
**Discovery**: System uses Ignition/Gazebo Sim, not classic Gazebo.

**Diagnostic Commands**:
```bash
ign topic -i -t /front/scan  # Check topic info
ign topic -e -t /world/simple_test_world/stats -n 1  # Check simulation status
```

**Result**:
- Topic exists: `tcp://172.17.0.1:41449, ignition.msgs.LaserScan`
- Simulation running: `sim_time: 203s, iterations: 203682`
- **But topic not publishing data!**

### Phase 3: Root Cause Identification

#### 8. Sensor Type Configuration Error
**Root Cause**: Sensor type configuration in `<gazebo>` tag in URDF incorrect.

**Incorrect Configuration**:
```xml
<gazebo reference="front_lidar_link">
    <sensor type="ray" name="front_lidar_sensor">  <!-- Wrong: ray -->
        ...
    </sensor>
</gazebo>
```

**Correct Configuration**:
```xml
<gazebo reference="front_lidar_link">
    <sensor type="gpu_ray" name="front_lidar_sensor">  <!-- Correct: gpu_ray -->
        ...
    </sensor>
</gazebo>
```

**Difference**:
- `ray` - CPU ray sensor (classic Gazebo)
- `gpu_ray` - GPU ray sensor (Gazebo Sim/Ignition)

**Modified Location**: `src/external/scout_ros2/scout_description/urdf/scout_mini.xacro`

**Modified Content**:
```bash
# Before
<sensor type="ray" name="front_lidar_sensor">
<sensor type="ray" name="rear_lidar_sensor">

# After
<sensor type="gpu_ray" name="front_lidar_sensor">
<sensor type="gpu_ray" name="rear_lidar_sensor">
```

**Result**: ✅ Success! LiDAR data publishing normally:
- Gazebo side: `ign topic -e -t /front/scan -n 1` has data output
- ROS side: `ros2 topic echo /front/scan --qos-profile sensor_data --once` has data output
- Data frequency: ~10Hz

### Phase 4: RViz Laser Display Issue

#### 9. Simulation Time Misalignment
**Problem**: Gazebo uses simulation time (/clock topic), but RViz defaults to system time, causing TF query failure.

**Error Log**:
```
[rviz2]: Message Filter dropping message: frame 'scout_mini/base_link/front_lidar_sensor' at time 2427.900 for reason 'discarding message because the queue is full'
```

**Solution**: Added `use_sim_time` parameter to RViz node:
```python
rviz_node = Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    arguments=['-d', rviz_config],
    parameters=[{'use_sim_time': use_sim_time}],  # Added
    output='screen')
```

**Result**: Partial fix, but RViz still cannot display laser point cloud.

#### 10. Frame ID Mismatch Issue
**Problem**:
- Laser data frame_id is: `scout_mini/base_link/front_lidar_sensor` (Gazebo automatically adds model name prefix)
- TF tree frame is: `front_lidar_link` (URDF definition)
- Mismatch causes RViz to fail finding coordinate system transformation

**Error Log**:
```
[rviz2]: Message Filter dropping message: frame 'scout_mini/base_link/front_lidar_sensor' at time 2427.900 for reason 'discarding message because the queue is full'
```

**Diagnostic Process**:
```bash
# Check TF tree
ros2 run tf2_tools view_frames
# Result: scout_mini/base_link/front_lidar_sensor not in TF tree

# Check laser data frame_id
ros2 topic echo /front/scan --qos-profile sensor_data --once
# Result: header.frame_id = "scout_mini/base_link/front_lidar_sensor"
```

**Solution**: Added static TF transformation to map Gazebo frame to URDF frame:
```python
# Static TF publisher - maps Gazebo sensor frame to URDF frame
# Gazebo automatically adds model name prefix to sensor frame_id
# Laser data is in frame: scout_mini/base_link/front_lidar_sensor
# URDF frame is: front_lidar_link
# Transform from sensor frame to URDF frame
front_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='front_lidar_static_tf',
    arguments=[
        '0.245', '0', '0.14',  # xyz (position of sensor relative to base_link)
        '0', '0', '0',         # rpy
        'front_lidar_link',                    # parent frame (URDF frame)
        'scout_mini/base_link/front_lidar_sensor'  # child frame (Gazebo frame)
    ]
)

# Static TF publisher for rear lidar
rear_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='rear_lidar_static_tf',
    arguments=[
        '-0.245', '0', '0.14',  # xyz (position of sensor relative to base_link)
        '0', '0', '0',          # rpy
        'rear_lidar_link',                     # parent frame (URDF frame)
        'scout_mini/base_link/rear_lidar_sensor'  # child frame (Gazebo frame)
    ]
)
```

**TF Chain**:
```
base_link 
  └── front_lidar_link
        └── scout_mini/base_link/front_lidar_sensor (laser data frame)
```

**Result**: ✅ Success! RViz correctly displays laser point cloud:
- Fixed Frame set to `base_link`
- LaserScan topic set to `/front/scan` or `/rear/scan`
- Laser point cloud correctly displayed around robot

## Final Result
✅ **Complete Success!**

- ✅ Gazebo side laser data publishing normally (~10Hz)
- ✅ ROS side receiving laser data
- ✅ RViz correctly displays laser point cloud
- ✅ Laser point cloud matches obstacle positions

## Modified Files List

1. **scout_mini_gazebo.launch.py**
   - Modified: Environment variable setting order (moved before Gazebo starts)
   - Modified: Gazebo resource path configuration (use parent directory)
   - Modified: RViz node added `use_sim_time` parameter
   - Added: Python os module import
   - Added: front_lidar_static_tf node
   - Added: rear_lidar_static_tf node

2. **simple_test_world.world**
   - Added: sensors-system plugin
   - Added: scene-broadcaster-system plugin
   - Added: user-commands-system plugin
   - Added: 4 obstacle boxes
   - Upgraded: SDF version from 1.6 to 1.8

3. **scout_mini.xacro**
   - Modified: Front LiDAR sensor type from `ray` to `gpu_ray`
   - Modified: Rear LiDAR sensor type from `ray` to `gpu_ray`
   - Confirmed: Added `<always_on>true</always_on>` configuration

## Experience Summary

### Gazebo Simulation Environment Configuration
1. **Gazebo Sim vs Classic Gazebo**: Different Gazebo versions use different sensor type names
   - Classic Gazebo uses `ray`
   - Gazebo Sim/Ignition uses `gpu_ray`

2. **Environment Variable Order**: Must set resource paths before Gazebo starts
   - `GZ_SIM_RESOURCE_PATH`
   - `IGN_GAZEBO_RESOURCE_PATH`
   - `GAZEBO_MODEL_PATH`

3. **World File Completeness**: Must include all necessary system plugins
   - sensors-system: Sensor processing
   - scene-broadcaster-system: Scene broadcasting
   - user-commands-system: User commands

4. **Resource Path Format**: Gazebo's `model://` URI needs correct directory structure
   - Needs to point to parent directory containing `model_name/subdirectory`
   - Not directly to `meshes` directory

### ROS2-Gazebo Bridge
5. **QoS Configuration**: Sensor data typically uses BestEffort strategy
   - Use `qos_sensor_data: True` parameter

6. **Simulation Time Sync**: All nodes should use same clock source
   - Use `use_sim_time` parameter to ensure time consistency

7. **Frame ID Mapping**: Gazebo automatically adds model name prefix to sensor frame
   - Need to establish mapping via static TF
   - Or manually set Fixed Frame to complete Gazebo frame in RViz

### TF Tree Maintenance
8. **Static TF Direction**: TF transformation direction is important
   - parent_frame → child_frame
   - For Gazebo sensors: sensor_frame → URDF_frame

9. **Coordinate Position**: Ensure TF transformation position matches URDF joint position
   - front_lidar: x=0.245, y=0, z=0.14
   - rear_lidar: x=-0.245, y=0, z=0.14

## Test Verification Commands

```bash
# Rebuild
cd /home/luoyongkang/scout_nav2_mini
colcon build --symlink-install

# Run launch file
source install/setup.bash
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# Test Gazebo side laser data
ign topic -e -t /front/scan -n 1

# Test ROS side laser data
ros2 topic echo /front/scan --qos-profile sensor_data --once

# Check data frequency
ros2 topic hz /front/scan

# Check TF tree
ros2 run tf2_tools view_frames

# Check TF transformation
ros2 run tf2_ros tf2_echo base_link front_lidar_link
```

## RViz Configuration Steps

1. Add LaserScan display
   - Click "Add" → "By topic" → Select "/front/scan"

2. Set Fixed Frame
   - Set to `base_link`

3. Adjust display parameters
   - Size (m): 0.1
   - Style: Points
   - Queue Size: 10

### Phase 5: Teleop Cannot Control Robot Motion

#### 11. Problem Description
**Issue**: Robot displays normally in Gazebo, LiDAR data is normal, but robot does not move after sending `/cmd_vel` commands via `teleop-twist-keyboard`.

#### 12. Initial Suspicions: World Plugin Conflicts
**Hypothesis**: Explicitly declared `scene-broadcaster-system` and `user-commands-system` plugins in world file conflict with Gazebo's default loaded plugins.

**Attempts**:
- Removed `scene-broadcaster-system` and `user-commands-system` → Gazebo GUI completely blank
- Removed only `user-commands-system` → Robot cannot spawn/display
- Kept only `sensors-system` → Gazebo GUI blank and robot not displayed

**Result**: Proved both plugins are essential, but issue unresolved.

#### 13. Key Discovery: `server.config` Default Loading Behavior
**Diagnostic Command**:
```bash
cat /usr/share/ignition/ignition-gazebo6/server.config
```

**Discovery**:
```xml
<server_config>
  <plugins>
    <plugin entity_name="*" entity_type="world" filename="ignition-gazebo-physics-system" name="gz::sim::systems::Physics"></plugin>
    <plugin entity_name="*" entity_type="world" filename="ignition-gazebo-user-commands-system" name="gz::sim::systems::UserCommands"></plugin>
    <plugin entity_name="*" entity_type="world" filename="ignition-gazebo-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"></plugin>
  </plugins>
</server_config>
```

**Conclusion**:
- Ignition Gazebo 6 (Fortress) **only loads 3 system plugins by default**: Physics, UserCommands, SceneBroadcaster
- **When any `<plugin>` declaration appears in the world file, Gazebo stops loading default plugins from `server.config`**
- Original world file explicitly declared Sensors + SceneBroadcaster + UserCommands, but **lacked the Physics system**

#### 14. Attempts to Add Physics and Contact Systems
**Issue**: Robot on ground but cannot move when world plugins are kept. Suspected Physics not loaded or missing Contact system.

**Attempted Solutions**:
- Added `contact-system` to world → Still cannot move
- Added `physics-system` to world → Still cannot move

**Key Discovery**: World file used `gz-sim-*` naming (e.g., `gz-sim-physics-system`), while `server.config` uses `ignition-gazebo-*` naming. In Ignition Fortress, `gz-sim-*` is **not a valid alias** for all plugins.

#### 15. Correct Plugin Filenames and Add Missing Plugins
**Correct Configuration**:
```xml
<plugin filename="ignition-gazebo-sensors-system" name="gz::sim::systems::Sensors">
    <rendering>false</rendering>
    <sensor_update_rate>10</sensor_update_rate>
</plugin>
<plugin filename="ignition-gazebo-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"></plugin>
<plugin filename="ignition-gazebo-user-commands-system" name="gz::sim::systems::UserCommands"></plugin>
<plugin filename="ignition-gazebo-contact-system" name="gz::sim::systems::Contact"></plugin>
<plugin filename="ignition-gazebo-physics-system" name="gz::sim::systems::Physics"></plugin>
```

**Modified Location**: `simple_test_world.world`

**Result**: ✅ Success! Robot can receive `/cmd_vel` commands and move normally. LiDAR data normal. Gazebo GUI normal.

---

## Modified Files List (Additional)

4. **simple_test_world.world** (modified again)
   - Modified: All plugin filenames from `gz-sim-*` to `ignition-gazebo-*`
   - Added: `contact-system` plugin (collision detection/friction)
   - Added: `physics-system` plugin (physics engine)

5. **scout_mini_gazebo.launch.py** (refactored)
   - Fixed: ros_gz_bridge message types from `ignition.msgs.*` to `gz.msgs.*`
   - Unified: Single `gz_bridge` node replacing multiple separate bridge instances
   - Removed: Redundant `joint_state_publisher` node (Gazebo plugin already publishes)
   - Removed: Redundant `tf_to_odom.py` node (diff drive plugin already publishes `/odom`)

6. **scout_mini.xacro** (restored)
   - Restored: Reverted incorrectly modified scout_mini.xacro to original base model
   - Removed: Gazebo plugins and LiDAR definitions from scout_description package to keep it clean

7. **scout_mini_gazebo.xacro** (new file)
   - New: Integrated Scout Mini base model + dual LiDAR + Gazebo plugins (diff drive, joint state publisher, gpu_ray sensors)

8. **CMakeLists.txt**
   - Added: `urdf` directory to install
   - Removed: Obsolete `scout_diff_drive_controller.py` and `tf_to_odom.py` installations

---

## Experience Summary (Additional)

### Gazebo World File System Plugin Configuration
10. **Explicit plugin declarations in world suppress default loading**:
    - When any `<plugin>` tag exists in world file, Gazebo no longer loads default plugins from `server.config`
    - All required plugins must be explicitly declared in the world file

11. **Ignition Fortress plugin filename naming**:
    - Must use `ignition-gazebo-*` format (e.g., `ignition-gazebo-physics-system`)
    - `gz-sim-*` format is **not a valid alias** in Ignition Fortress

12. **Required explicit plugins for Ignition Fortress world files**:
    - `ignition-gazebo-physics-system`: Physics engine (diff drive dependency)
    - `ignition-gazebo-scene-broadcaster-system`: Scene broadcasting (GUI rendering dependency)
    - `ignition-gazebo-user-commands-system`: User commands (model spawn dependency)
    - `ignition-gazebo-contact-system`: Contact detection (wheel friction dependency)
    - `ignition-gazebo-sensors-system`: Sensor system (LiDAR dependency)

### ROS-Gazebo Bridge
13. **Message type namespace**: `ros-humble-ros-gz-bridge` uses `gz.msgs.*`, not `ignition.msgs.*`
    - Example: `/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist`

### Diff Drive Plugin
14. **Diff drive depends on Physics system**:
    - Even if `/cmd_vel` topic bridges correctly, if Physics system is not loaded, diff drive joint velocity commands cannot be converted to actual motion
    - Robot may appear "on the ground" (proper spawn height), but no physics simulation is actually running

---

## Test Verification Commands (Additional)

```bash
# Test keyboard control
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Check if /cmd_vel has data
ros2 topic echo /cmd_vel

# Check if /odom has data
ros2 topic echo /odom

# Check Gazebo default config file
cat /usr/share/ignition/ignition-gazebo6/server.config
```

## Date
2026-06-09 ~ 2026-06-11
