#!/usr/bin/env python3
"""
Nav2 Real Robot Launch — Nav2 stack only (no Gazebo).

Assumes the real robot drivers (scout_base) are already running and
publishing /odom, /front/scan, /joint_states, etc.

Usage:
    ros2 launch scout_mini_dual_lidar_gazebo nav2_real_robot_launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_nav2 = get_package_share_directory('scout_mini_dual_lidar_gazebo')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # ============================================================
    # Launch arguments
    # ============================================================
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    use_rviz = LaunchConfiguration('use_rviz')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='false',
        description='Use simulation clock if true (MUST be false for real robot)')

    declare_map_yaml = DeclareLaunchArgument(
        'map', default_value=os.path.join(pkg_nav2, 'maps', 'my_map.yaml'),
        description='Full path to map yaml file')

    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_nav2, 'config', 'real_robot', 'nav2_params.yaml'),
        description='Full path to Nav2 params file (real robot config)')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Launch RViz2 for visualization')

    # ============================================================
    # Nav2 navigation stack (NO Gazebo nodes — real robot only)
    # ============================================================
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='lifecycle_manager_navigation', output='screen',
        parameters=[{'use_sim_time': use_sim_time, 'autostart': True,
                     'node_names': ['map_server', 'amcl', 'planner_server',
                                    'controller_server', 'recoveries_server',
                                    'bt_navigator', 'waypoint_follower']}])

    map_server = Node(
        package='nav2_map_server', executable='map_server',
        name='map_server', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time, 'yaml_filename': map_yaml_file}])

    amcl = Node(
        package='nav2_amcl', executable='amcl',
        name='amcl', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    planner_server = Node(
        package='nav2_planner', executable='planner_server',
        name='planner_server', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    controller_server = Node(
        package='nav2_controller', executable='controller_server',
        name='controller_server', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    recoveries_server = Node(
        package='nav2_behaviors', executable='behavior_server',
        name='recoveries_server', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    bt_navigator = Node(
        package='nav2_bt_navigator', executable='bt_navigator',
        name='bt_navigator', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time,
                     'default_nav_to_pose_bt_xml': os.path.join(pkg_nav2, 'config', 'navigate_no_init_check.xml'),
                     'default_nav_through_poses_bt_xml': os.path.join(pkg_nav2, 'config', 'navigate_no_init_check.xml')}])

    waypoint_follower = Node(
        package='nav2_waypoint_follower', executable='waypoint_follower',
        name='waypoint_follower', output='screen',
        parameters=[params_file, {'use_sim_time': use_sim_time}])

    # RViz2
    nav2_rviz_config = os.path.join(pkg_nav2_bringup, 'rviz', 'nav2_default_view.rviz')
    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2', output='screen',
        arguments=['-d', nav2_rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz))

    # ============================================================
    # Assemble launch description
    # ============================================================
    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_map_yaml)
    ld.add_action(declare_params_file)
    ld.add_action(declare_use_rviz)

    # Nav2 nodes only — NO Gazebo, NO bridges, NO frame fixers
    ld.add_action(lifecycle_manager)
    ld.add_action(map_server)
    ld.add_action(amcl)
    ld.add_action(planner_server)
    ld.add_action(controller_server)
    ld.add_action(recoveries_server)
    ld.add_action(bt_navigator)
    ld.add_action(waypoint_follower)
    ld.add_action(rviz)

    return ld
