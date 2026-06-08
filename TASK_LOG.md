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