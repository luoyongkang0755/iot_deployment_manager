# Scout Mini Dual LiDAR Navigation2 (ROS2)

## Project Objectives
- Integrate two LiDAR sensors (front/rear or left/right) for the **Scout Mini** robot to build a redundant perception system.
- Based on **ROS2 Humble** and **Nav2** framework, implement autonomous navigation, obstacle avoidance, and path planning in indoor/outdoor environments.
- Support Gazebo simulation and real robot deployment, providing dual LiDAR data fusion and switching logic.
- Include complete launch files, parameter configurations, maps, and bag recording examples for easy reproduction and secondary development.
- Finally achieve safe passage through narrow corridors and real-time dynamic obstacle avoidance.

# ROS 2 Humble Docker Environment

## Run GUI Tools from Docker

This environment supports running graphical interface tools such as RViz2 and Gazebo within Docker containers.

### Prerequisites (Host Machine)

#### Linux (Ubuntu 22.04)
```bash
# Install X11 related tools
sudo apt-get update
sudo apt-get install -y x11-xserver-utils

# Allow Docker to access X11 server
xhost +local:docker
```