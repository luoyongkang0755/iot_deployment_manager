#!/bin/bash

echo "=== 检查激光雷达话题频率 ==="
timeout 5 ros2 topic hz /front/scan || echo "话题没有数据"

echo ""
echo "=== 检查激光雷达话题详细信息 ==="
ros2 topic info /front/scan -v

echo ""
echo "=== 检查激光雷达话题QoS配置 ==="
ros2 topic info /front/scan | grep -A 10 "QoS profile"

echo ""
echo "=== 尝试使用sensor_data QoS订阅 ==="
timeout 3 ros2 topic echo /front/scan --qos-profile sensor_data --once || echo "使用sensor_data QoS也没有数据"

echo ""
echo "=== 检查Gazebo传感器状态 ==="
gz model -m scout_mini -s 2>/dev/null || echo "无法获取模型传感器信息"

echo ""
echo "=== 检查激光雷达传感器是否在Gazebo中运行 ==="
gz sensor -l 2>/dev/null | grep lidar || echo "无法获取传感器列表"