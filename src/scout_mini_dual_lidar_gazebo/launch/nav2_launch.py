#!/usr/bin/env python3
"""
Nav2 Launch File for Scout Mini with Gazebo Simulation
Starts Gazebo + robot + Nav2 navigation stack in one launch file.

Usage:
    ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, EnvironmentVariable
from launch.substitutions import FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    # Package paths
    pkg_nav2 = get_package_share_directory('scout_mini_dual_lidar_gazebo')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    pkg_scout_description = get_package_share_directory('scout_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # ============================================================
    # Launch arguments
    # ============================================================
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    world = LaunchConfiguration('world')
    model = LaunchConfiguration('model')
    verbose = LaunchConfiguration('verbose')
    use_rviz = LaunchConfiguration('use_rviz')
    rviz_config = LaunchConfiguration('rviz_config')
    spawn_yaw = LaunchConfiguration('spawn_yaw')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true')

    declare_map_yaml = DeclareLaunchArgument(
        'map',
        default_value=os.path.abspath(os.path.join(pkg_nav2, 'maps', 'my_map.yaml')),
        description='Full path to map yaml file')

    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_nav2, 'config', 'nav2_params.yaml'),
        description='Full path to Nav2 params file')

    declare_world = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_nav2, 'worlds', 'simple_test_world.world'),
        description='Full path to the world model file to load')

    declare_model = DeclareLaunchArgument(
        'model',
        default_value=os.path.join(pkg_nav2, 'urdf', 'scout_mini_gazebo.xacro'),
        description='Full path to the robot URDF/XACRO file')

    declare_verbose = DeclareLaunchArgument(
        'verbose',
        default_value='false',
        description='Enable verbose output')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2 for visualization')

    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(pkg_nav2, 'rviz', 'display.rviz'),
        description='Path to RViz configuration file')

    declare_spawn_yaw = DeclareLaunchArgument(
        'spawn_yaw',
        default_value='3.14159',
        description='Initial yaw angle (radians) for robot spawn')

    # ============================================================
    # Gazebo environment variables
    # ============================================================
    scout_description_parent = os.path.dirname(pkg_scout_description)
    # Parent dir that contains the piper_description package share dir, so
    # Gazebo can resolve model://piper_description/meshes/*.STL.
    pkg_piper_description = get_package_share_directory('piper_description')
    piper_description_parent = os.path.dirname(pkg_piper_description)
    gz_resource_path = (
        scout_description_parent + ':' +
        piper_description_parent + ':' +
        pkg_nav2 + '/worlds')

    set_env_vars = [
        SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=gz_resource_path),
        SetEnvironmentVariable(name='IGN_GAZEBO_RESOURCE_PATH', value=gz_resource_path),
        SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=scout_description_parent),
    ]

    # ============================================================
    # Robot description (URDF via xacro)
    # ============================================================
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        model,
        ' mesh_prefix:=file://' + pkg_scout_description,
    ])
    robot_description = {'robot_description': ParameterValue(robot_description_content, value_type=str)}

    # ============================================================
    # Gazebo simulation nodes
    # ============================================================
    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': use_sim_time}])

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-v 4 ', world] if verbose else world,
        }.items(),
    )

    # NOTE: no ROS-side joint_state_publisher here. Gazebo's
    # gz-sim-joint-state-publisher-system (in scout_mini.gazebo) already
    # publishes /joint_states for ALL joints (wheels + Piper joint1..8)
    # with real physics angles; joint damping/friction keeps the arm at
    # zero pose. A second ROS publisher on the same topic would conflict.
    # Stage 5: joint_state_broadcaster (ros2_control) replaces the Gazebo
    # plugin as the single joint-state source.

    # Spawn robot in Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'scout_mini',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.181',
            '-Y', spawn_yaw,
        ],
        output='screen')

    # ROS-Gazebo bridges
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='gz_bridge',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'qos_overrides./front/scan.subscription.reliability': 'best_effort',
            'qos_overrides./rear/scan.subscription.reliability': 'best_effort',
        }],
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom_raw@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/front/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/rear/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ])

    # Sensor processing nodes
    scan_frame_fixer = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='scan_frame_fixer.py',
        name='scan_frame_fixer',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    imu_odom_corrector = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='imu_odom_corrector.py',
        name='imu_odom_corrector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    odom_to_tf = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='odom_to_tf.py',
        name='odom_to_tf',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    laser_merger = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='laser_merger.py',
        name='laser_merger',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ============================================================
    # Nav2 navigation stack
    # ============================================================
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'autostart': True,
                     'node_names': [
                         'map_server',
                         'amcl',
                         'planner_server',
                         'controller_server',
                         'recoveries_server',
                         'bt_navigator',
                         'waypoint_follower',
                     ]}])

    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time,
                     'yaml_filename': map_yaml_file}])

    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time}])

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time}])

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time}])

    recoveries_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='recoveries_server',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time}])

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time,
                     'default_nav_to_pose_bt_xml':
                         os.path.join(pkg_nav2, 'config', 'navigate_no_init_check.xml'),
                     'default_nav_through_poses_bt_xml':
                         os.path.join(pkg_nav2, 'config', 'navigate_no_init_check.xml')}])

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[params_file,
                    {'use_sim_time': use_sim_time}])

    # RViz2：默认使用本包 rviz_config（可通过 rviz_config launch arg 覆盖）
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz))

    # ============================================================
    # Assemble launch description
    # ============================================================
    ld = LaunchDescription()

    # Environment variables (MUST be set before Gazebo starts)
    for env_var in set_env_vars:
        ld.add_action(env_var)

    # Launch arguments
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_map_yaml)
    ld.add_action(declare_params_file)
    ld.add_action(declare_world)
    ld.add_action(declare_model)
    ld.add_action(declare_verbose)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_rviz_config)
    ld.add_action(declare_spawn_yaw)

    # Gazebo + robot
    ld.add_action(gazebo)
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn_entity)
    ld.add_action(gz_bridge)
    ld.add_action(scan_frame_fixer)
    ld.add_action(imu_odom_corrector)
    ld.add_action(odom_to_tf)
    ld.add_action(laser_merger)

    # Nav2 navigation stack
    ld.add_action(map_server)
    ld.add_action(amcl)
    ld.add_action(planner_server)
    ld.add_action(controller_server)
    ld.add_action(recoveries_server)
    ld.add_action(bt_navigator)
    ld.add_action(waypoint_follower)
    ld.add_action(lifecycle_manager)

    # RViz
    ld.add_action(rviz)

    return ld
