#!/bin/bash

echo "=== 检查ROS2话题列表 ==="
ros2 topic list | grep scan

echo ""
echo "=== 检查Gazebo话题列表 ==="
gz topic -l | grep scan

echo ""
echo "=== 检查front/scan话题信息 ==="
ros2 topic info /front/scan

echo ""
echo "=== 检查Gazebo端front/scan话题 ==="
gz topic -e /model/scout_mini/front/scan --once 2>/dev/null || echo "Gazebo话题 /model/scout_mini/front/scan 不存在"

echo ""
echo "=== 检查Gazebo端/front/scan话题 ==="
gz topic -e /front/scan --once 2>/dev/null || echo "Gazebo话题 /front/scan 不存在"

echo ""
echo "=== 检查桥接节点状态 ==="
ros2 node list | grep bridge