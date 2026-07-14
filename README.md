# Scout Mini Dual LiDAR Navigation2 (ROS2)

## Project Objectives
- Integrate two LiDAR sensors (front/rear) for the **Scout Mini** robot to build a redundant perception system.
- Based on **ROS2 Humble** and **Nav2** framework, implement autonomous navigation, obstacle avoidance, and path planning.
- Support Gazebo simulation with complete launch files, parameter configurations, and maps.

---

## Quick Start

### 1. Build the Workspace

```bash
cd ~/scout_nav2_mini
colcon build --symlink-install
source install/setup.bash
```

### 2. Launch Nav2 Full Stack (Gazebo Simulation + Navigation)

```bash
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py
```

A single command starts: Gazebo world + Scout Mini robot + dual LiDAR + Nav2 navigation stack + RViz2.

### 3. Send Three Navigation Goals (Task 22 Test)

```bash
ros2 run scout_mini_dual_lidar_gazebo send_nav2_goals.py
```

Sends three goal poses sequentially via the `/navigate_to_pose` action server, automatically recording success/failure and elapsed time.

**To modify goals**: Edit the `GOALS` list at the top of `src/scout_mini_dual_lidar_gazebo/src/send_nav2_goals.py`.

---

## Project Structure

```
scout_nav2_mini/
├── src/
│   └── scout_mini_dual_lidar_gazebo/
│       ├── config/
│       │   ├── nav2_params.yaml              # Nav2 parameter configuration
│       │   └── navigate_no_init_check.xml    # Behavior tree XML
│       ├── launch/
│       │   ├── nav2_launch.py                # Nav2 full-stack launch file
│       │   └── scout_mini_gazebo.launch.py   # Gazebo simulation launch file
│       ├── maps/
│       │   └── my_map.yaml / my_map.pgm      # Navigation map
│       ├── worlds/
│       │   └── simple_test_world.world       # Gazebo world
│       ├── rviz/
│       │   └── display.rviz                  # RViz configuration
│       └── src/
│           ├── send_nav2_goals.py            # Three-goal test script
│           ├── laser_merger.py               # Dual LiDAR fusion
│           ├── odom_to_tf.py                 # Odometry TF publisher
│           ├── imu_odom_corrector.py         # IMU odometry correction
│           └── scan_frame_fixer.py           # Laser frame fixer
├── reports/
│   └── nav2_three_goal_results.md            # Task 22 test report
├── media/
│   ├── screenshots/                          # Screenshots
│   └── LOG/                                  # Terminal logs
└── TASK_LOG.md                               # Task log
```

---

## ROS 2 Humble Docker Environment

### Run GUI Tools from Docker

This environment supports running graphical interface tools such as RViz2 and Gazebo within Docker containers.

#### Prerequisites (Host Machine — Ubuntu 22.04)

```bash
sudo apt-get update
sudo apt-get install -y x11-xserver-utils
xhost +local:docker
```
