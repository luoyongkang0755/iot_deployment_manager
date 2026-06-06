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