#!/usr/bin/env python3
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Get package directories
    pkg_gazebo = get_package_share_directory('scout_mini_dual_lidar_gazebo')
    pkg_slam_toolbox = get_package_share_directory('slam_toolbox')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    slam_params_file = LaunchConfiguration('slam_params_file')
    world_file = LaunchConfiguration('world')

    # Declare arguments
    declared_args = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=os.path.join(pkg_gazebo, 'params', 'slam_toolbox_params.yaml'),
            description='Full path to the ROS2 parameters file to use for the SLAM Toolbox node'),
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(pkg_gazebo, 'worlds', 'simple_test_world.world'),
            description='Full path to the world model file to load'),
    ]

    # Include Gazebo launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'scout_mini_gazebo.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'world': world_file,
        }.items(),
    )

    # SLAM Toolbox node
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': use_sim_time},
        ],
    )

    # RViz2 node
    rviz_config = os.path.join(pkg_gazebo, 'rviz', 'slam.rviz')
    if not os.path.exists(rviz_config):
        rviz_config = ''

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config] if rviz_config else [],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    ld = LaunchDescription(declared_args)
    ld.add_action(gazebo_launch)
    ld.add_action(slam_toolbox_node)
    ld.add_action(rviz_node)

    return ld