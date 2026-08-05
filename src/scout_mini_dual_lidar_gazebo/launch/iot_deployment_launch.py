#!/usr/bin/env python3
"""IoT deployment 端到端 launch（含 Stage 5 抓取放置）。

包含现有 nav2_launch.py（Gazebo + Nav2 + RViz），
并启动 deployment_approach_node（候选生成/过滤/评分/导航编排）、
ros2_control controller spawner（joint_state_broadcaster / arm / gripper）
以及 manipulation_node（取货 -> 等待 -> 放置）。

启动顺序：
  1. nav2_launch 拉起 Gazebo；ign_ros2_control 插件在其中创建
     /controller_manager。
  2. controller spawner 注册为事件处理器，在 /controller_manager 出现后
     才加载并激活各 controller（保证 controller 先就绪）。
  3. manipulation_node 在 action server 可用后才开始发轨迹。

Usage:
    ros2 launch scout_mini_dual_lidar_gazebo iot_deployment_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    TimerAction,
)
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

    # ------------------------------------------------------------------
    # Stage 5: ros2_control controller spawners（加载并激活）
    # ign_ros2_control 在 Gazebo 内提供 /controller_manager。Gazebo 首次
    # 启动较慢，统一加大 --switch-timeout。三个 spawner 用 TimerAction
    # 错开启动（每个间隔 10s），避免并发 switch 冲突；
    # joint_state_broadcaster 先于轨迹 controller。
    # ------------------------------------------------------------------
    controllers_yaml = os.path.join(pkg_share, 'config', 'piper_controllers.yaml')
    spawner_args = [
        '--controller-manager', '/controller_manager',
        '--param-file', controllers_yaml,
        '--switch-timeout', '90',
    ]

    jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='spawner_joint_state_broadcaster',
        output='screen',
        arguments=['joint_state_broadcaster'] + spawner_args,
    )

    arm_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='spawner_arm_controller',
        output='screen',
        arguments=['arm_controller'] + spawner_args,
    )

    gripper_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='spawner_gripper_controller',
        output='screen',
        arguments=['gripper_controller'] + spawner_args,
    )

    # JSB -> arm -> gripper，每个间隔 10s，给前一个足够时间完成
    delayed_jsb = TimerAction(period=10.0, actions=[jsb_spawner])
    delayed_arm = TimerAction(period=20.0, actions=[arm_spawner])
    delayed_gripper = TimerAction(period=30.0, actions=[gripper_spawner])

    # ------------------------------------------------------------------
    # Stage 5: manipulation node
    # 在 controller 加载链启动后运行；节点内部会等 action server 就绪再动。
    # ------------------------------------------------------------------
    manipulation_node = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='manipulation_node.py',
        name='manipulation_node',
        output='screen',
        parameters=[
            os.path.join(pkg_share, 'config', 'manipulation_waypoints.yaml'),
            {'use_sim_time': True},
        ],
    )

    delayed_manipulation = TimerAction(period=45.0, actions=[manipulation_node])

    # ------------------------------------------------------------------
    # Stage 5: spawn the IoT device.
    # Spawn poses are parameterised in manipulation_waypoints.yaml.
    # ------------------------------------------------------------------
    import yaml
    with open(os.path.join(pkg_share, 'config', 'manipulation_waypoints.yaml')) as f:
        _wp = yaml.safe_load(f)['manipulation_node']['ros__parameters']

    iot_spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_iot_device',
        output='screen',
        arguments=[
            '-file', os.path.join(pkg_share, 'worlds', 'iot_device.sdf'),
            '-name', 'iot_device',
            '-x', str(_wp['iot_spawn_x']),
            '-y', str(_wp['iot_spawn_y']),
            '-z', str(_wp['iot_spawn_z']),
            '-Y', str(_wp['iot_spawn_yaw']),
        ],
    )
    delayed_iot_spawn = TimerAction(period=6.0, actions=[iot_spawn])

    return LaunchDescription([
        nav2_launch,
        deployment_node,
        delayed_iot_spawn,
        delayed_jsb,
        delayed_arm,
        delayed_gripper,
        delayed_manipulation,
    ])
