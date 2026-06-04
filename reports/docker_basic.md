# Docker Basics and ROS 2 Humble Minimal Environment Report

## What is Docker?
Docker is an open-source containerization platform that allows developers to package applications and their dependencies into a lightweight, portable container. Containers share the host operating system kernel but achieve process isolation and resource limits through namespaces and control groups (cgroups).

## Why Use Docker?
- **Reproducibility**: Docker containers provide exactly the same runtime environment regardless of the Linux distribution, avoiding "it works on my machine" issues.
- **Isolation**: Operations inside containers do not affect the host machine, making it easy to test different software versions or configurations.
- **Easy Distribution**: Through Dockerfiles or image repositories, teams can quickly share ready-to-use development environments.
- **Resource Efficiency**: Compared to virtual machines, containers do not require simulating a complete operating system, booting faster and consuming less memory.

## What does the Dockerfile install/configure?
This Dockerfile is based on `ros:humble-ros-base` (contains ROS 2 Humble core packages, Ubuntu 22.04 base system), with the following additional operations:

1. **Install Tools**  
   - `python3-colcon-common-extensions`: Provides the `colcon` command-line tool for building ROS 2 workspaces.  
   - `build-essential`: Provides compilation toolchains like `gcc`, `g++`, `make`.

2. **Environment Setup**  
   - Added `source /opt/ros/humble/setup.bash` to `~/.bashrc`, so the ROS 2 environment takes effect automatically each time entering the container.

3. **Create Workspace and Example Package**  
   - Created `/ros2_ws/src` directory as the source space for the ROS 2 workspace.  
   - Generated a python package named `my_package` (ament_python type) using `ros2 pkg create`. This package contains a standard `package.xml` and can be built normally by `colcon build`.

4. **Working Directory Setup**  
   - Set the default working directory of the image to `/ros2_ws`, so users can directly run `colcon build` after entering the container.

## Verification Method
1. Execute `bash docker/run_container.sh` to start the container.  
2. Execute `colcon build` inside the container.  
3. Observe the output and see success messages like "Summary: 1 package finished" (see attachment `media/LOG/task7.log`).  
4. Build artifacts are located in `/ros2_ws/build`, `/ros2_ws/install`, and other directories.