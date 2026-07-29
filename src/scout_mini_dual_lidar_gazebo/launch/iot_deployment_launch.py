#!/usr/bin/env python3
"""IoT deployment 端到端 launch。

包含现有 nav2_launch.py（Gazebo + Nav2 + RViz），
并启动 deployment_approach_node（候选生成/过滤/评分/导航编排）。

Usage:
    ros2 launch scout_mini_dual_lidar_gazebo iot_deployment_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('scout_mini_dual_lidar_gazebo')

    # 包含现有 Nav2 + Gazebo launch，RViz 用 iot_deployment.rviz
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'nav2_launch.py')),
        launch_arguments={
            'rviz_config': os.path.join(pkg_share, 'rviz', 'iot_deployment.rviz'),
        }.items(),
    )

    # deployment_approach_node，加载 deployment_params.yaml
    deployment_node = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='deployment_approach_node.py',
        name='deployment_approach_node',
        output='screen',
        parameters=[
            os.path.join(pkg_share, 'config', 'deployment_params.yaml'),
            {'use_sim_time': True},
        ],
    )

    return LaunchDescription([
        nav2_launch,
        deployment_node,
    ])
