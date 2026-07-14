# Task Log

## [2026-06-03] Repository Initialization
- Created repository `scout_mini_nav2`
- Initialized Git repository and added the following files:
  - `README.md`: Project objectives description
  - `TASK_LOG.md`: This log file
  - `.gitignore`: Ignore temporary/compiled files
- Established standard ROS2 workspace directory structure:
  `src/`, `maps/`, `worlds/`, `config/`, `launch/`, `bags/`, `media/screenshots/`, `reports/`, `docker/`
- Completed first commit: `Initialize Scout Mini dual LiDAR Nav2 assignment repository`
- Associated remote repository and pushed to `master` branch

## [2026-06-04] Task 2: Basic Linux Terminal Commands

### What was done
- Executed `pwd`, `ls`, `mkdir test_folder`, `touch test_folder/test.txt`, `echo "ROS learning task" > test_folder/test.txt`, `cat test_folder/test.txt`, `rm -r test_folder` in sequence at the project root directory.
- Compiled detailed reports of each command's output and explanation, saved as `reports/linux_basic_commands.md`.

### Command List
1. `pwd` – Display current directory
2. `ls` – List directory contents
3. `mkdir test_folder` – Create test folder
4. `touch test_folder/test.txt` – Create empty file
5. `echo "..." > test_folder/test.txt` – Write content
6. `cat test_folder/test.txt` – Read file content
7. `rm -r test_folder` – Recursively delete test folder

### What worked/failed
- All commands executed successfully with no errors.
- `rm -r` should be used with caution. Only temporary test directories were deleted this time, without affecting project files.

### What was learned
- Understood that `pwd` shows absolute path and `ls -la` can view hidden files.
- Learned to use `>` redirection to quickly generate configuration files.
- Remembered that `rm -r` permanently deletes, always confirm the path before operation.

# Task 3 — Create Basic ROS 2 Workspace Package

## Objectives
Understand ROS 2 workspace structure and create the first package.

## Created Package
- **Package Name**: `ros2_learning_examples`
- **Location**: `src/ros2_learning_examples/`
- **Build Type**: `ament_python`

## Key Commands
```bash
# Enter the src directory of the workspace
cd src

# Create Python package
ros2 pkg create ros2_learning_examples --build-type ament_python

# Return to workspace root directory
cd ..

# Build workspace
colcon build

# Load environment settings
source install/setup.bash

# Verify package installation
ros2 pkg list | grep ros2_learning_examples
```

## [2025-06-04] Task 4 – ROS 2 Publisher and Subscriber

### What was done
- Created a Python publisher node (`basic_publisher.py`) that publishes `"Learning ROS 2 topics"` to the topic `/student_status` at 1 Hz.
- Created a Python subscriber node (`basic_subscriber.py`) that listens to `/student_status` and prints received messages.
- Verified communication using ROS 2 command-line tools.

### Commands used
```bash
# Build the workspace (if needed)
cd ~/scout_mini_dual_lidar_nav2
colcon build --packages-select ros2_learning_examples
source install/setup.bash

# Run publisher (terminal 1)
ros2 run ros2_learning_examples basic_publisher

# Run subscriber (terminal 2)
ros2 run ros2_learning_examples basic_subscriber

# Topic inspection (terminal 3)
ros2 topic list
ros2 topic echo /student_status
ros2 topic hz /student_status
```

## Task 5 — ROS 2 Launch File

**Objective**: Launch both publisher and subscriber nodes with a single launch file.

**Completed**:
- Created file: `src/ros2_learning_examples/launch/basic_pubsub.launch.py`
- Wrote Python launch script using `LaunchDescription` and `Node` actions to launch both nodes simultaneously.

**Launch File Explanation**:
ROS 2 launch files are used to launch multiple nodes at once and can configure node parameters, namespaces, remappings, etc. Key advantages include:
- **Simplified launch process**: Avoid executing `ros2 run` in multiple terminals; launch the entire system with one command.
- **Centralized management**: Unified settings for node output, environment variables, parameter files, etc.
- **Improved reproducibility**: Node combinations are solidified as code, facilitating team collaboration and experiment reproduction.
- **Conditional launch and events**: Dynamically decide whether to launch a node based on conditions (e.g., device detection).

This launch file specifically implements:
- Launches both publisher node (`talker_node`) and subscriber node (`listener_node`) simultaneously.
- Sets `output='screen'` to display node print information directly in the terminal.
- Ensures real-time message refresh via `emulate_tty=True`.

**Verification Steps**:
1. Execute command in terminal: `ros2 launch ros2_learning_examples basic_pubsub.launch.py`
2. Observe both nodes launching simultaneously and outputting communication logs.
3. Open another terminal, use `ros2 node list` to see `/talker_node` and `/listener_node`.
4. Use `ros2 topic echo /chatter` to confirm normal topic message transmission.

**Evidence**: Launch output screenshot (`task5`) shows publisher sending messages and subscriber receiving successfully.

# Task 6 — TF Basics Report

## 1. What is TF Coordinate?

TF (Transform) is a core tool in ROS 2 for managing relative position and pose relationships between different coordinate systems. It maintains a **TF Tree**, where each node represents a coordinate system, and each directed edge represents a transformation (translation + rotation) from one coordinate system to another.

Through TF, data in any coordinate system (e.g., LiDAR point cloud, camera image) can be converted to another coordinate system in real-time. For example, obstacle coordinates detected by LiDAR can be automatically converted to the robot's central coordinate system for navigation algorithms.

## 2. Three Important Coordinate Systems in Robots

- **`base_link`**  
  A coordinate system fixed on the robot body, usually with its origin at the robot's geometric center or rotation center. It moves with the robot and serves as the reference frame for describing the installation positions of all sensors, joints, and other components on the vehicle.

- **`odom` (Odometry Coordinate System)**  
  A **local coordinate system** derived from the robot's internal sensors (e.g., wheel encoders, IMU). This coordinate system accumulates drift over time but has relatively high short-term accuracy. The transformation between `odom` and `base_link` directly reflects the robot's motion increment from odometry.

- **`map` (Map Coordinate System)**  
  A **global fixed coordinate system** built from external sensors (e.g., LiDAR, GPS), free from drift. It is the absolute reference frame that the robot ultimately expects to use for navigation tasks.

**Typical relationship between the three**:  
`map → odom → base_link`  
- `map → odom`: Corrects long-term odometry drift (provided by SLAM or localization module).  
- `odom → base_link`: Real-time estimation from odometry, providing smooth short-term motion estimation.

## 3. Why LiDAR Needs to Connect to `base_link`?

LiDAR (`front_lidar_link`) is a physical sensor fixed at a specific position on the robot. Its measurement data (e.g., `[x, y]` obstacle coordinates) is given relative to its own coordinate system (origin at LiDAR center). However, the robot's decision-making system needs to know the position of these obstacles relative to the robot body for proper obstacle avoidance and path planning.

Therefore, a static transform (`static_transform_publisher`) must be established via TF to explicitly inform the system: **the fixed spatial relationship between `base_link` and `front_lidar_link`**. This allows `tf2_ros` to automatically convert LiDAR data to `base_link`, achieving unification of sensor data and robot body.

## 2026-6-4 Task 7 - Minimal ROS 2 Humble Docker Environment

- **Status**: Completed
- **Content**:
  - Wrote `docker/Dockerfile`: Based on `ros:humble-ros-base`, installed colcon and build tools, created `/ros2_ws` workspace, and generated example package `my_package`.
  - Wrote `docker/run_container.sh`: Builds image and runs container in interactive mode.
  - Wrote `reports/docker_basic.md`: Explains Docker concepts, usage, and software installed by Dockerfile.
  - Generated build output example `build_output.log`.
- **Verification Result**: Running `bash docker/run_container.sh` to enter container and executing `colcon build` succeeded with expected output.
- **Committed Files**:
  - docker/Dockerfile
  - docker/run_container.sh
  - reports/docker_basic.md
  - media/LOG/task7.log
  - TASK_LOG

## 2026-06-04: Task 8 - Docker GUI Support (RViz2 / Gazebo)

- **Status**: Completed
- **Content**:
  - Updated `docker/run_container.sh`: Added X11 forwarding, display variables, permission configuration
  - Created `docker/docker-compose.yml`: Provides Docker Compose deployment method
  - Updated `docker/Dockerfile`: Installed rviz2, gazebo, and GUI dependencies
  - Updated `README.md`: Added "Run GUI Tools from Docker" section with prerequisites, usage, and troubleshooting
  - Created `screenshots/` directory with screenshot descriptions
- **Verification Commands** (executed inside container):
  - `rviz2` ✓ Successfully launched GUI window
  - `gazebo` ✓ Successfully launched simulation environment
- **Evidence**: Screenshots saved in `screenshots/` directory
- **Committed Files**:
  - docker/run_container.sh (updated)
  - docker/docker-compose.yml (new)
  - docker/Dockerfile (updated)
  - README.md (updated)
  - screenshots/rviz2.png
  - screenshots/gazebo.png
  - TASK_LOG (updated)

# Task 9
2026-06-03: Scout ROS 2 Package Integration
- Cloned official Scout ROS2 packages to `src/external/scout_ros2/` (from https://github.com/agilexrobotics/scout_ros2.git)
- Identified and analyzed three Scout packages:
  * `scout_msgs`: Message definition package, compiled successfully ✅
  * `scout_description`: URDF robot model (V2 and Mini), includes mesh files, compiled successfully ✅
  * `scout_base`: Control driver package, missing ugv_sdk external dependency ⚠️
- Build verification: `colcon build --packages-select scout_msgs scout_description scout_base ros2_learning_examples`
  * Successfully compiled: ros2_learning_examples (0.80s), scout_description (0.93s), scout_msgs (3.87s)
  * Failed: scout_base (missing ugv_sdk dependency, expected behavior)
- Verification package installation: `ros2 pkg list | grep scout` outputs scout_description and scout_msgs ✅
- Found launch files:
  * scout_description/launch/scout_base_description.launch.py (URDF publication)
  * scout_base/launch/scout_base.launch.py, scout_mini_base.launch.py, scout_mini_omni_base.launch.py (driver launch)
- Created detailed report `reports/scout_ros2_package_review.md`, including:
  * Function description and dependency relationships of the three packages
  * URDF/xacro and mesh file locations
  * Launch file descriptions
  * ugv_sdk dependency solution
  * Usage examples (RViz visualization, driver launch)

# Task 10 — Launch Scout Mini Model in RViz2

## Objective
Verify that the Scout Mini robot model is visible in RViz2.

## Issues Fixed
**1. Missing Scout Mini model**: The cloned `scout_description` package only contained `scout_v2.xacro`, no Scout Mini model existed.
**2. Incorrect DAE file paths**: The xacro files referenced `package://scout_description/meshes/scout_v2/*.dae`, but the actual mesh files are located directly in `meshes/` directory.

## Files Modified/Created
- **Modified**: `scout_description/urdf/scout_v2.xacro` - Fixed mesh path from `meshes/scout_v2/base_link.dae` to `meshes/base_link.dae`
- **Modified**: `scout_description/urdf/scout_wheel_type1.xacro` - Fixed wheel mesh path
- **Modified**: `scout_description/urdf/scout_wheel_type2.xacro` - Fixed wheel mesh path
- **Created**: `scout_description/urdf/scout_mini.xacro` - New Scout Mini model with appropriate dimensions
- **Created**: `scout_description/launch/display.launch.py` - RViz2 display launch file with robot_state_publisher, joint_state_publisher, and rviz2 nodes

## Key Commands
```bash
# Build the scout_description package
colcon build --packages-select scout_description
source install/setup.bash

# Launch Scout Mini model in RViz2
ros2 launch scout_description display.launch.py

# Launch Scout V2 model (optional)
ros2 launch scout_description display.launch.py model:=scout_v2.xacro

# Verify robot description
ros2 topic echo /robot_description --once

# View TF tree
ros2 run tf2_tools view_frames
```

## Verification Results
- ✅ Scout Mini model visible in RViz2
- ✅ TF tree shows correct structure (base_link, base_footprint, inertial_link, wheel links)
- ✅ Robot description topic published correctly
- ✅ Joint states published correctly

## Evidence
- RViz2 screenshot showing Scout Mini model (`screenshots/task10_rviz.png`)
- TF tree image (`screenshots/task10_tf_tree.png`)
- Terminal output logs (`media/LOG/task10.log`)

## Committed Files
- scout_description/urdf/scout_v2.xacro (updated)
- scout_description/urdf/scout_wheel_type1.xacro (updated)
- scout_description/urdf/scout_wheel_type2.xacro (updated)
- scout_description/urdf/scout_mini.xacro (new)
- scout_description/launch/display.launch.py (new)
- TASK_LOG.md (updated)

# Task 11 — Launch Scout Mini in Gazebo

## Objective
Launch Scout Mini robot into Gazebo simulation world.

## Issues Fixed
**1. Missing `ros_gz_sim` package**: Docker image didn't include `ros-humble-ros-gz-sim`, causing CMake configuration error.
**2. Gazebo Fuel download failure**: World file used `model://` URI which required online download, fixed by using inline model definitions.
**3. DAE mesh file path resolution**: `package://` URI not resolved by Gazebo, fixed by using `file://` absolute path via xacro parameter.
**4. Robot position**: Initial spawn z=0.1 caused wheels to sink into ground, corrected to z=0.205.

## Files Created/Modified
- **Created**: `src/scout_mini_dual_lidar_gazebo/` - New ROS2 package for Gazebo simulation
  - `package.xml` - Package dependencies (scout_description, ros_gz_sim, robot_state_publisher)
  - `CMakeLists.txt` - CMake build configuration, installs launch and worlds directories
  - `launch/scout_mini_gazebo.launch.py` - Gazebo launch file
- **Created**: `worlds/simple_test_world.world` - SDF world file with inline ground plane and sun
- **Modified**: `scout_description/urdf/scout_mini.xacro` - Added `mesh_prefix` parameter for mesh path
- **Modified**: `scout_description/urdf/scout_wheel_type1.xacro` - Use `${mesh_prefix}` for mesh path
- **Modified**: `scout_description/urdf/scout_wheel_type2.xacro` - Use `${mesh_prefix}` for mesh path
- **Modified**: `docker/Dockerfile` - Added `ros-humble-ros-gz-sim` package, configured Tsinghua mirrors for rosdep

## Launch File Explanation (`scout_mini_gazebo.launch.py`)

The launch file orchestrates the entire Gazebo simulation startup process:

### 1. Package Path Resolution
```python
pkg_scout_description = get_package_share_directory('scout_description')
pkg_scout_gazebo = get_package_share_directory('scout_mini_dual_lidar_gazebo')
pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
```
Gets installation paths for required packages.

### 2. Launch Arguments Declaration
- `world`: Path to Gazebo world file (default: `simple_test_world.world`)
- `model`: Path to robot URDF/XACRO file (default: `scout_mini.xacro`)
- `use_sim_time`: Use simulation clock (default: `true`)
- `verbose`: Enable detailed Gazebo output (default: `false`)

### 3. Robot Description Generation
```python
robot_description_content = Command([
    PathJoinSubstitution([FindExecutable(name='xacro')]),
    ' ',
    model,
    ' mesh_prefix:=file://' + pkg_scout_description,
])
```
Executes xacro to convert XACRO to URDF, passing `mesh_prefix` parameter with absolute file path for Gazebo compatibility.

### 4. Robot State Publisher Node
```python
node_robot_state_publisher = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[robot_description, {'use_sim_time': use_sim_time}])
```
Publishes `/robot_description` topic and TF transforms based on URDF.

### 5. Gazebo Launch
```python
gazebo = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
    launch_arguments={'gz_args': world}.items())
```
Includes official Gazebo launch file, loads specified world.

### 6. Spawn Entity Node
```python
spawn_entity = Node(
    package='ros_gz_sim',
    executable='create',
    arguments=['-name', 'scout_mini', '-topic', 'robot_description',
               '-x', '0.0', '-y', '0.0', '-z', '0.205'])
```
Reads robot model from `/robot_description` topic and spawns into Gazebo at position (0, 0, 0.205).

### 7. Environment Variables
```python
SetEnvironmentVariable(
    name='GZ_SIM_RESOURCE_PATH',
    value=pkg_scout_description + '/meshes:' + pkg_scout_gazebo + '/worlds')
```
Sets Gazebo resource search paths for mesh files.

## Startup Sequence
```
1. Declare launch arguments
      ↓
2. Set environment variables (GZ_SIM_RESOURCE_PATH)
      ↓
3. Launch Gazebo (load world file)
      ↓
4. Start robot_state_publisher (publish URDF + TF)
      ↓
5. Spawn robot entity in Gazebo
```

## Key Commands
```bash
# Build the package
colcon build --packages-select scout_description scout_mini_dual_lidar_gazebo
source install/setup.bash

# Launch Scout Mini in Gazebo
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# Launch with verbose output
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py verbose:=true

# Verify topics
ros2 topic list
ros2 topic echo /robot_description --once
ros2 run tf2_tools view_frames
```

## Verification Results
- ✅ Gazebo launches successfully with simple test world
- ✅ Scout Mini robot spawned in Gazebo with complete mesh model
- ✅ Robot positioned correctly on ground (wheels touch surface)
- ✅ TF tree published correctly (base_link, base_footprint, wheel links)
- ✅ No mesh file errors in Gazebo console

## Evidence
- Gazebo screenshot showing Scout Mini model (`media/screenshots/task11_gazebo.png`)
- TF tree image (`media/screenshots/task11_tf_tree.png`)
- Terminal output logs (`media/LOG/task11.log`)

## Committed Files
- src/scout_mini_dual_lidar_gazebo/package.xml (new)
- src/scout_mini_dual_lidar_gazebo/CMakeLists.txt (new)
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py (new)
- worlds/simple_test_world.world (new)
- scout_description/urdf/scout_mini.xacro (updated)
- scout_description/urdf/scout_wheel_type1.xacro (updated)
- scout_description/urdf/scout_wheel_type2.xacro (updated)
- docker/Dockerfile (updated)
- TASK_LOG.md (updated)

---

## Task 12 — Remote Control Scout Mini

### Objective
Verify that the robot can move using keyboard teleoperation.

### Problem Description
teleop_twist_keyboard can publish `/cmd_vel` topic, but the robot cannot move. Checking revealed `Subscription count: 0`, meaning there was no subscriber. Later discovered that Gazebo DiffDrive plugin does not publish `/odom` topic directly, and odometry data needs to be obtained via TF transformation.

### Root Cause
1. **Topic name mismatch**: teleop_twist_keyboard publishes `/cmd_vel`, Gazebo DiffDrive plugin subscribes to `/model/scout_mini/cmd_vel`
2. **Gazebo plugin does not publish odom topic**: DiffDrive plugin publishes odometry information via TF instead of a separate `/odom` topic

### Solution
1. **URDF configuration**: Gazebo DiffDrive plugin directly subscribes to `/cmd_vel`
2. **ROS-Gazebo bridge**: `cmd_vel_bridge` bridges ROS2 `/cmd_vel` to Gazebo
3. **TF to odometry**: `tf_to_odom` node subscribes to `/model/scout_mini/tf` and converts to standard `nav_msgs/Odometry` published to `/odom`

## Task 13 - Add Front RS-AIRY LiDAR

### Objective
Add and verify front LiDAR simulation.

### Required Transformation
- x = 0.5, y = 0.0, z = 0.25, roll=0, pitch=0, yaw=0

### Modified Files
- `scout_mini.xacro` - Add front_lidar_link and Gazebo ray sensor plugin

### Topics
- `/front/scan` - Front LiDAR scan data

### Coordinate Frame
- `front_lidar_link`

### Verification Results
- ✅ `/front/scan` topic publishing correctly
- ✅ TF transform base_link → front_lidar_link working

### Key Commands
```bash
ros2 topic list | grep scan    # Check scan topics
ros2 topic echo /front/scan --once    # View single scan data
ros2 topic hz /front/scan    # Check scan frequency
ros2 run tf2_ros tf2_echo base_link front_lidar_link    # Check TF transform
```

---

## Task 14 - Add Rear RS-AIRY LiDAR

### Objective
Complete dual LiDAR simulation setup.

### Required Transformation
- x = -0.5, y = 0.0, z = 0.25, roll=0, pitch=0, yaw = 3.1416 (π rad)

### Modified Files
- `scout_mini.xacro` - Add rear_lidar_link and Gazebo ray sensor plugin
- `scout_mini_gazebo.launch.py` - Add ros_gz_bridge nodes

### Topics
- `/rear/scan` - Rear LiDAR scan data

### Coordinate Frame
- `rear_lidar_link`

### Verification Results
- ✅ `/rear/scan` topic publishing correctly
- ✅ TF transform base_link → rear_lidar_link working

### Key Commands
```bash
ros2 topic echo /rear/scan --once    # View single scan data
ros2 topic hz /rear/scan    # Check scan frequency
ros2 run tf2_ros tf2_echo base_link rear_lidar_link    # Check TF transform
ros2 run tf2_tools view_frames    # View TF tree
```

### Launch File Updates

#### Added Bridge Nodes
```python
# Bridge /cmd_vel from ROS2 to Gazebo
cmd_vel_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist'])

# Bridge /odom from Gazebo to ROS2
odom_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/odom[nav_msgs/msg/Odometry@ignition.msgs.Odometry'])
```

#### Bridge Syntax Explanation
- `]` indicates ROS2 → Gazebo one-way
- `[` indicates Gazebo → ROS2 one-way
- Original `@` symbol was for bidirectional bridging, but we only need one-way here

#### URDF Plugin Configuration
```xml
<gazebo>
    <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
        <left_joint>rear_left_wheel</left_joint>
        <right_joint>rear_right_wheel</right_joint>
        <wheel_separation>0.52</wheel_separation>
        <wheel_radius>0.145</wheel_radius>
        <topic>/cmd_vel</topic>
        <odometry_topic>/odom</odometry_topic>
    </plugin>
</gazebo>
```

### Control Topic Details
- **Topic Name**: `/cmd_vel`
- **Message Type**: `geometry_msgs/msg/Twist`
- **Structure**:
  ```
  linear:
    x: forward/backward speed (m/s)
    y: lateral speed (m/s)
    z: vertical speed (m/s)
  angular:
    x: roll (rad/s)
    y: pitch (rad/s)
    z: yaw/turn speed (rad/s)
  ```

### Key Commands
```bash
# Rebuild the package
colcon build --packages-select scout_description scout_mini_dual_lidar_gazebo
source install/setup.bash

# Launch Gazebo simulation
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# In another terminal: Start keyboard teleoperation
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Verify topics
ros2 topic info /cmd_vel
# Should show Subscription count: 1

ros2 topic echo /cmd_vel
ros2 topic echo /odom
```

### Teleoperation Instructions
| Key | Action |
|-----|--------|
| `i` | Move forward |
| `k` | Move backward |
| `j` | Turn left |
| `l` | Turn right |
| `u` | Move forward-left |
| `o` | Move forward-right |
| `m` | Move backward-left |
| `,` | Move backward-right |
| `q` | Increase speed by 10% |
| `z` | Decrease speed by 10% |
| `space` | Stop |

### Verification Results
- ✅ `ros2 topic info /cmd_vel` shows Subscription count: 1
- ✅ Robot can move using keyboard teleoperation in Gazebo
- ✅ `/odom` topic publishes odometry data normally
- ✅ Topic info shows correct publishers and subscribers
- ✅ Twist messages are correctly formatted with linear.x and angular.z values

### Evidence
- Terminal output showing /cmd_vel messages
- Teleop terminal showing key controls
- Node list showing cmd_vel_bridge and odom_bridge are running

### Committed Files
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py (updated)
- src/scout_mini_dual_lidar_gazebo/src/tf_to_odom.py (added)
- src/scout_mini_dual_lidar_gazebo/CMakeLists.txt (updated)
- src/scout_mini_dual_lidar_gazebo/package.xml (updated)
- src/external/scout_ros2/scout_description/urdf/scout_mini.xacro (updated)
- TASK_LOG.md (updated)

---

## Task 15 — Dual LiDAR Validation

### Objective
Verify that both LiDAR sensors are working correctly and can be visualized in RViz2.

### Verification Items

#### 1. Front LiDAR
- **Topic Name**: `/front/scan`
- **Message Type**: `sensor_msgs/msg/LaserScan`
- **Frame ID**: `scout_mini/base_link/front_lidar_sensor`
- **TF Chain**: `base_link` → `front_lidar_link` → `scout_mini/base_link/front_lidar_sensor`
- **Position**: x=0.245, y=0, z=0.14

#### 2. Rear LiDAR
- **Topic Name**: `/rear/scan`
- **Message Type**: `sensor_msgs/msg/LaserScan`
- **Frame ID**: `scout_mini/base_link/rear_lidar_sensor`
- **TF Chain**: `base_link` → `rear_lidar_link` → `scout_mini/base_link/rear_lidar_sensor`
- **Position**: x=-0.245, y=0, z=0.14

#### 3. Frequency Verification
```bash
# Front LiDAR
$ ros2 topic hz /front/scan
average rate: 9.894
	min: 0.096s max: 0.104s std dev: 0.00230s window: 11

# Rear LiDAR  
$ ros2 topic hz /rear/scan
average rate: 9.876
	min: 0.096s max: 0.105s std dev: 0.00197s window: 21
```

#### 4. RViz2 Visualization
- **Fixed Frame**: `base_link`
- **Display Type**: LaserScan
- **Topics**: `/front/scan` and `/rear/scan`
- **Screenshot**: `media/screenshots/task15.png`

### Root Cause of Previous Issues
1. **Frame ID mismatch**: Gazebo automatically adds model name prefix (`scout_mini/base_link/front_lidar_sensor`) while URDF defines `front_lidar_link`
2. **TF chain broken**: No transformation from `front_lidar_link` to `scout_mini/base_link/front_lidar_sensor`

### Solution
Added static TF transformations in launch file:
```python
# Front LiDAR static TF
front_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    arguments=['0.245', '0', '0.14', '0', '0', '0',
               'front_lidar_link', 'scout_mini/base_link/front_lidar_sensor'])

# Rear LiDAR static TF
rear_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    arguments=['-0.245', '0', '0.14', '0', '0', '0',
               'rear_lidar_link', 'scout_mini/base_link/rear_lidar_sensor'])
```

### Verification Results
- ✅ Front LiDAR publishes valid data on `/front/scan`
- ✅ Rear LiDAR publishes valid data on `/rear/scan`
- ✅ Both coordinate frames connected to `base_link`
- ✅ RViz2 can visualize both scans correctly
- ✅ Data frequency stable at ~10Hz

### Committed Files
- reports/dual_lidar_validation.md (new)
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py (updated)
- TASK_LOG.md (updated)

---

## Task 16 — Navigation World Creation

### Objective
Create a controlled Gazebo world for Nav2 testing with walls, obstacles, and sufficient navigation space for Scout Mini.

### World Design

#### Boundary Walls (16m x 16m area)
- **North Wall**: Position (0, 8.0, 0.75), Size (16.0 x 0.3 x 1.5)
- **South Wall**: Position (0, -8.0, 0.75), Size (16.0 x 0.3 x 1.5)
- **East Wall**: Position (8.0, 0, 0.75), Size (0.3 x 16.0 x 1.5)
- **West Wall**: Position (-8.0, 0, 0.75), Size (0.3 x 16.0 x 1.5)

#### Obstacles (6 colored boxes)
| Obstacle | Position | Size | Color | Purpose |
|----------|----------|------|-------|---------|
| obstacle_box_1 | (4.0, 0.0, 0.5) | 1.0x1.0x1.0 | Red | Front center obstacle |
| obstacle_box_2 | (0.0, 4.0, 0.3) | 0.8x0.8x0.6 | Green | Left side obstacle |
| obstacle_box_3 | (0.0, -4.0, 0.4) | 1.2x0.6x0.8 | Blue | Right side obstacle |
| obstacle_box_4 | (-4.0, 0.0, 0.6) | 0.8x1.5x1.2 | Yellow | Rear obstacle |
| obstacle_box_5 | (3.0, 3.0, 0.4) | 0.7x0.7x0.8 | Purple | Front-left corner |
| obstacle_box_6 | (-3.0, -3.0, 0.5) | 0.9x0.9x1.0 | Orange | Rear-right corner |

#### Navigation Waypoints
- **waypoint_1 (Green)**: Position (5.0, 5.0, 0.05)
- **waypoint_2 (Blue)**: Position (-5.0, -5.0, 0.05)

### Obstacle Placement Strategy
1. **Central Navigation Space**: Robot starts at origin (0,0) with 4m clearance in all directions
2. **Avoidance Training**: Obstacles placed at varying distances to test obstacle avoidance
3. **Path Planning**: Multiple paths available between obstacles for navigation testing
4. **LiDAR Testing**: Obstacles of different sizes provide good LiDAR scanning targets

### Navigation Space Calculation
- **Total area**: 16m x 16m = 256 m²
- **Clear space around origin**: ~4m radius = ~50 m²
- **Obstacle coverage**: ~8 m² (6 obstacles)
- **Remaining navigable space**: ~200 m²

### Verification Results
- ✅ World starts successfully in Gazebo
- ✅ All 4 boundary walls visible
- ✅ All 6 obstacles visible and properly placed
- ✅ Scout Mini has sufficient navigation space (4m clearance from origin)
- ✅ Ground plane with proper friction settings
- ✅ Sensors system plugin loaded

### Committed Files
- src/scout_mini_dual_lidar_gazebo/worlds/simple_test_world.world (updated)
- TASK_LOG.md (updated)

---

## Task 17 — Map Preparation for Nav2 (with Simulation Debugging)

### Objective
Build a map using SLAM Toolbox, resolve critical simulation issues, and prepare map files for Nav2 navigation.

### Key Issues Fixed

#### 1. World Plugin Conflict Preventing Robot Motion
**Symptom**: Robot displayed normally in Gazebo, LiDAR working, but `teleop-twist-keyboard` cannot control motion.

**Root Cause**: Ignition Gazebo 6 (Fortress) `server.config` only loads 3 system plugins by default: Physics, UserCommands, SceneBroadcaster. When any `<plugin>` appears in world file, defaults are suppressed. Original world file only declared Sensors + SceneBroadcaster + UserCommands, **missing Physics system**, so diff drive plugin couldn't convert velocity commands to actual motion.

**Fix**:
- Explicitly declare 5 required plugins in `simple_test_world.world`
- Changed plugin filenames from `gz-sim-*` to `ignition-gazebo-*` (Ignition Fortress requirement)

#### 2. Message Type Namespace Mismatch
**Issue**: ros_gz_bridge message type configuration incorrect — `gz.msgs.*` doesn't match Gazebo's internal `ignition.msgs.*` types.

**Fix**:
- Gazebo → ROS direction (odom/tf/joint_states): use `ignition.msgs.*`
- ROS → Gazebo direction (cmd_vel): use `gz.msgs.*`

#### 3. TF Tree Disconnection
**Issue**: Gazebo diff drive publishes `scout_mini/odom -> scout_mini/base_link` (with model name prefix), while robot_state_publisher publishes `base_link -> front_lidar_link` etc (without prefix). Two TF trees have no connection.

**Fix**: Added two identity static TF transforms:
- `odom -> scout_mini/odom` (connects odom chain)
- `scout_mini/base_link -> base_link` (connects base_link chain)

#### 4. SLAM Toolbox Parameter Mismatch
**Fix**:
- `map_name: scout_mini_map` → `map_name: map` (matches Nav2 default `/map` topic)
- `minimum_time_interval: 0.5` → `0.25` (matches 5Hz LiDAR)
- Added `mode: mapping`

#### 5. LiDAR Frequency Optimization
**Change**: Reduced LiDAR update_rate from 10Hz to 5Hz to reduce CPU load.

#### 6. Map Saving
**Issue**: `maps/` directory didn't exist, `map_saver_cli` threw file write error.

**Fix**: `mkdir -p maps/` then successfully saved 791×957 map (0.05 m/pixel).

### Modified Files

| File | Action | Description |
|------|--------|-------------|
| [worlds/simple_test_world.world](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/worlds/simple_test_world.world) | Modified | Explicitly declare 5 system plugins (ignition-gazebo-* format), sensor_update_rate=5 |
| [launch/scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py) | Refactored | Unified bridges, fixed message types, added model prefix static TFs |
| [urdf/scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro) | New | Integrated base model + dual LiDAR + Gazebo plugins |
| [urdf/scout_mini.xacro](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/urdf/scout_mini.xacro) | Restored | Restored to clean base model |
| [params/slam_toolbox_params.yaml](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/params/slam_toolbox_params.yaml) | Modified | Optimized params (map_name/mode/minimum_time_interval) |
| [launch/slam.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/slam.launch.py) | Refactored | Only launches SLAM, no Gazebo/RViz |
| [launch/display.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/launch/display.launch.py) | Fixed | Pass mesh_prefix, point to correct RViz config |
| [rviz/display.rviz](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/rviz/display.rviz) | New | RViz config with Fixed Frame=base_link |
| [CMakeLists.txt](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/CMakeLists.txt) | Modified | Install urdf and rviz directories |

### Generated Map Files
- `maps/nav2_test_map.pgm` — Map image (791×957, 0.05 m/pixel)
- `maps/nav2_test_map.yaml` — Map metadata

### Usage Flow

```bash
# 1. Launch simulation
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 2. Launch SLAM (new terminal)
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py

# 3. Teleop for mapping (new terminal)
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 4. Save map (after map appears in RViz)
mkdir -p maps
ros2 run nav2_map_server map_saver_cli -f maps/nav2_test_map
```

### Verification Commands

```bash
# Check TF tree completeness
ros2 run tf2_tools view_frames

# Check /map topic
ros2 topic echo /map --once

# Check Gazebo default config
cat /usr/share/ignition/ignition-gazebo6/server.config

# Check Gazebo internal message types
ign topic -i -t /tf
ign topic -i -t /odom
```

### Key Takeaways

1. **Explicit world plugins suppress default loading**: Must declare all required plugins
2. **Ignition Fortress uses `ignition-gazebo-*` filenames**: `gz-sim-*` is not a valid alias
3. **Gazebo prepends model name to frame_ids**: Need static TF to bridge naming
4. **`ros-humble-ros-gz-bridge` types must match Gazebo**: Use `ign topic -i` to verify

### Verification Results
- ✅ Robot can be teleoperated in Gazebo
- ✅ Dual LiDAR data publishing (5Hz)
- ✅ SLAM mapping working, `/map` topic has data
- ✅ TF tree fully connected: `map → odom → base_link → sensors`
- ✅ Map saved as pgm + yaml files
- ✅ RobotModel displays correctly in RViz


---

## Task 18 — Navigation Coordinate Frames Explanation (Reworked)

### Objective
Ensure understanding of the Nav2 coordinate frame chain, including the model name prefix bridging mechanism discovered during Task 17 debugging.

### Updated Reports
- `reports/navigation_frames.md` — Comprehensive explanation (updated for actual TF tree)
- `reports/frames_chinese.md` — Chinese version (updated for actual TF tree)

### Actual TF Tree (After Task 17 Prefix Bridge Fix)

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → [front_lidar_link, rear_lidar_link]
  SLAM    static identity      diff drive plugin      static identity    robot_state_publisher
```

Gazebo automatically prepends `scout_mini/` to all frame IDs. Two static identity TF transforms bridge the namespaces:
- `odom → scout_mini/odom` — connects ROS standard to Gazebo-scoped odom
- `scout_mini/base_link → base_link` — connects Gazebo-scoped to ROS standard base_link

### Key Frames Explained

#### 1. map Frame (World Frame)
- **Origin**: Map origin (world-fixed)
- **Characteristics**: Globally fixed, may jump on re-localization, maintained by SLAM/AMCL
- **Usage**: Global path planning, long-term navigation

#### 2. odom Frame (Odometry Frame)
- **Origin**: Robot's starting position
- **Characteristics**: Continuous and smooth (50 Hz), high short-term precision, unbounded long-term drift
- **Usage**: Local path tracking, real-time motion control

#### 3. Gazebo Prefix Frames (scout_mini/odom, scout_mini/base_link)
- **Origin**: Gazebo diff drive plugin output with model name prefix
- **Characteristics**: Zero-offset identity transforms bridge to ROS standard frames
- **Purpose**: Connect Gazebo's name-scoped TF publishing to ROS standard naming

#### 4. base_link Frame (Robot Body Frame)
- **Location**: Robot geometric center, 0.145m above ground
- **Characteristics**: Moves with robot, parent of all URDF-defined sensor frames
- **Usage**: Sensor fusion reference, motion control

#### 5. base_footprint Frame
- **Location**: Vertical projection of base_link onto ground (z = -0.145m)
- **Usage**: 2D navigation and costmap reference

#### 6. LiDAR Frames
- **front_lidar_link**: (0.245, 0, 0.14) relative to base_link, forward-facing, 360° scan, 5 Hz
- **rear_lidar_link**: (-0.245, 0, 0.14) relative to base_link, rear-facing (180° yaw), 360° scan, 5 Hz

### Key Differences

#### map vs odom

| Characteristic | map | odom |
|----------------|-----|------|
| **Origin** | World-fixed map origin | Robot's start position |
| **Continuity** | Discontinuous (may jump) | Continuous and smooth |
| **Accuracy** | Long-term (loop closure) | Short-term (drifts unbounded) |
| **Update Rate** | ~2–10 Hz (SLAM) | 50 Hz (diff drive) |
| **Publisher** | SLAM Toolbox / AMCL | Gazebo → ros_gz_bridge |
| **Usage** | Global planning | Local control |

**Why both needed**: `odom` provides smooth, high-frequency state. `map → odom` transform adjusts the drift offset so SLAM corrections don't disrupt live control.

### Verification Commands

```bash
ros2 run tf2_tools view_frames          # Full TF tree
ros2 run tf2_ros tf2_echo map front_lidar_link   # End-to-end check
ros2 run tf2_ros tf2_echo odom base_link         # Odometry chain
ros2 run tf2_ros tf2_echo base_link front_lidar_link  # Static transform
```

### Verification Results
- ✅ No disconnected frames — single connected TF tree from map to all leaves
- ✅ map vs odom clearly explained (discrete vs continuous)
- ✅ Model prefix bridging mechanism documented
- ✅ LiDAR frame positions verified against URDF
- ✅ All end-to-end transforms queryable

### Committed Files
- `reports/navigation_frames.md` (updated for actual TF tree)
- `reports/frames_chinese.md` (updated for actual TF tree)
- `TASK_LOG.md` (updated)

---
## Task 24 — Clean Build and Reproducibility Test

### Objective
Prove the project can be rebuilt from a clean state with zero errors.

### Commands

```bash
cd /ws
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

### Build Results

```
Summary: 6 packages finished [1.22s]
```

| Package | Result | Time |
|---------|--------|------|
| scout_msgs | Success | 0.48s |
| scout_description | Success | 0.33s |
| scout_mini_dual_lidar_gazebo | Success | 0.11s |
| ros2_learning_examples | Success | 1.07s |
| ugv_sdk | Success | 0.29s |
| scout_base | Success | 0.16s |

### Errors & Fixes

No errors. All 6 packages built on the first attempt, no manual intervention needed.

### Verification

```bash
source install/setup.bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py
```

### Submitted Files
- `reports/clean_build_test.md` (new)
- `TASK_LOG.md` (updated)

---
## Task 19 — Minimal Nav2 Launch

### Objective
Get Nav2 nodes launched and lifecycle nodes active before tuning navigation behavior.

### Created Files
- `config/nav2_params.yaml` — Minimal Nav2 parameter configuration
- `launch/nav2_launch.py` — Minimal Nav2 startup file

### Nodes Configured

| Node | Package | Purpose |
|------|---------|---------|
| `map_server` | nav2_map_server | Serve saved map (.pgm/.yaml) |
| `amcl` | nav2_amcl | Monte Carlo localization with /front/scan |
| `planner_server` | nav2_planner | Global path (NavFn planner) |
| `controller_server` | nav2_controller | Local path following (DWB controller) |
| `recoveries_server` | nav2_behaviors | Spin/backup/wait recovery |
| `bt_navigator` | nav2_bt_navigator | Behavior tree engine |
| `waypoint_follower` | nav2_waypoint_follower | Waypoint execution |
| `lifecycle_manager` | nav2_lifecycle_manager | Auto-activate all nodes |

### Key Configuration Details

**Robot Specs:**
- Base frame: `base_link`
- Odometry frame: `odom`
- Global frame: `map`
- LiDAR scan topic: `/front/scan`
- Robot model: differential drive
- Max velocity: 0.5 m/s linear, 1.0 rad/s angular

**Costmaps:**
- Resolution: 0.05 m/pixel (matches SLAM map)
- Robot radius: 0.3 m
- Local costmap: 3m × 3m rolling window at 5 Hz
- Global costmap: static map + laser obstacles

**Planner:** NavFn (basic grid-based A*)
**Controller:** DWB (Dynamic Window Approach)

### Usage

```bash
# Terminal 1: Launch Gazebo simulation
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# Terminal 2: Launch Nav2
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py

# In RViz: Set initial pose with "2D Pose Estimate"
# Then send goal with "Nav2 Goal"
```

### Verification Commands

```bash
ros2 node list                    # All 7 Nav2 nodes + lifecycle_manager + rviz
ros2 lifecycle nodes              # Check lifecycle states
ros2 topic list                   # /map, /cmd_vel, /plan, /local_plan, etc.
```

### Submitted Files
- `config/nav2_params.yaml` (new)
- `launch/nav2_launch.py` (new)
- `CMakeLists.txt` (updated — added config dir)
- `TASK_LOG.md` (updated)
- `TASK_LOG_CHINESE.md` (updated)


---

## Task 22 — Send Three Nav2 Goal Points

### Objective
Evaluate navigation behavior by sending at least three goal poses and documenting results.

### Files Created
- `reports/nav2_three_goal_results.md` — Test report with results table
- `src/send_nav2_goals.py` — Script to send three Nav2 goals sequentially

### How to Run

```bash
# Terminal 1: Launch Gazebo + Nav2
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py

# Terminal 2 (after Nav2 is fully up): Send three goals
ros2 run scout_mini_dual_lidar_gazebo send_nav2_goals.py
```

### Script Behavior
The `send_nav2_goals.py` script:
1. Sets the initial pose for AMCL localization
2. Waits 5 seconds for AMCL to converge
3. Sends Goal 1, waits for result, records success/failure + elapsed time
4. Sends Goal 2, same process
5. Sends Goal 3, same process
6. Prints a formatted summary table of all results

### Default Goal Points
| Goal | Position (x, y) | Description |
|------|------------------|-------------|
| 1 | (2.0, 0.0) | Forward 2m along +X |
| 2 | (-2.0, 2.0) | Navigate to quadrant II |
| 3 | (2.0, -2.0) | Navigate to quadrant IV |

**To modify goals**, edit the `GOALS` list at the top of `send_nav2_goals.py`.

### Evidence Required
- Video showing all three goal points (or three short videos)
- RViz2 screenshot for each goal point
- Nav2 terminal logs
- Filled-in `reports/nav2_three_goal_results.md`

### Submitted Files
- `reports/nav2_three_goal_results.md` (new)
- `src/send_nav2_goals.py` (new)
- `CMakeLists.txt` (updated)
- `TASK_LOG.md` (updated)


---

## Task 25 — Separate Simulation and Real Robot Configurations

### Objective
Prepare repository for future physical Scout Mini testing by separating simulation and real robot configs.

### Directory Structure Created

```
config/
├── simulation/
│   └── nav2_params.yaml           # Simulation Nav2 params (use_sim_time: True)
└── real_robot/
    └── nav2_params.yaml           # Real robot Nav2 params (use_sim_time: False)

launch/
├── simulation/
│   └── nav2_simulation_launch.py  # Full stack: Gazebo + robot + Nav2
└── real_robot/
    └── nav2_real_robot_launch.py  # Nav2 only (no Gazebo, no bridges)
```

### Key Differences

| Aspect | Simulation | Real Robot |
|--------|-----------|------------|
| Time source | `use_sim_time: True` | `use_sim_time: False` |
| Scan topic | `/merged/scan` (front+rear) | `/front/scan` |
| Velocities | 0.5 m/s linear, 1.0 rad/s angular | 0.3 m/s, 0.5 rad/s (conservative) |
| Odometry | Gazebo DiffDrive → correctors | `scout_base` driver directly |
| Sensor processing | `scan_frame_fixer`, `laser_merger` | Not needed |
| Gazebo bridges | Required | Not used |

### Real Robot Deployment Checklist

1. CAN interface: bring up `can0` at 500 kbps, launch `scout_base`
2. LiDAR: configure Ethernet IP, launch vendor driver
3. Emergency stop: verify physical E-stop works
4. First test: obstacle-free, low speed (0.3 m/s)
5. Frame verify: check `map → odom → base_link → front_lidar_link` TF chain

### Submitted Files
- `config/simulation/nav2_params.yaml` (new)
- `config/real_robot/nav2_params.yaml` (new)
- `launch/simulation/nav2_simulation_launch.py` (new)
- `launch/real_robot/nav2_real_robot_launch.py` (new)
- `reports/simulation_vs_real_robot.md` (new)
- `TASK_LOG.md` (updated)
