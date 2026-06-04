# Issue: RViz2 Not Displaying When Running `ros2 launch scout_description scout_base_description.launch.py`

## Description

When running `ros2 launch scout_description scout_base_description.launch.py`, the command executes successfully but RViz2 does not open. The launch file only starts `robot_state_publisher` but does not include an RViz2 node for visualization.

## Root Cause Analysis

After examining `scout_base_description.launch.py`, the launch file only starts:
- `robot_state_publisher` node (publishes `/robot_description` and TF transforms)

It does **not** include:
- `rviz2` node for visualization

## Expected Behavior

Running `ros2 launch scout_description scout_base_description.launch.py` should:
1. Start `robot_state_publisher` to publish the URDF model
2. Open RViz2 with a pre-configured view to display the robot model

## Actual Behavior

Only `robot_state_publisher` starts. No RViz2 window appears.

## Environment

- ROS 2 Humble
- Ubuntu 22.04
- scout_description package version: 0.1.0

## Steps to Reproduce

1. Build the workspace: `colcon build --packages-select scout_description`
2. Source the environment: `source install/setup.bash`
3. Run the launch command: `ros2 launch scout_description scout_base_description.launch.py`
4. Observation: Only terminal output shows robot_state_publisher starting, no RViz2 window appears

## Suggested Fix

Add an RViz2 node to the launch file with appropriate configuration:

```python
Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen',
    arguments=['-d', PathJoinSubstitution([FindPackageShare("scout_description"), "rviz", "scout_model.rviz"])]
)
```

Or at minimum, start RViz2 without a config:

```python
Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    output='screen'
)
```

## Additional Information

Current launch file contents (as of commit):
- Only contains `robot_state_publisher` node
- No RViz2 node included
- No joint_state_publisher for interactive joint manipulation

## Impact

Users cannot visualize the Scout robot model directly from the launch file. They must manually run `rviz2` separately and configure it to display the robot.
