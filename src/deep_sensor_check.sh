#!/bin/bash

echo "========================================"
echo "   深度传感器诊断"
echo "========================================"

echo ""
echo "--- 1. 检查传感器状态 ---"
echo "执行: ign topic -i -t /front/scan"
ign topic -i -t /front/scan 2>/dev/null || echo "无法获取话题信息"

echo ""
echo "--- 2. 检查Gazebo版本 ---"
gz version 2>/dev/null || echo "无法获取Gazebo版本"
ign version 2>/dev/null || echo "无法获取Ignition版本"

echo ""
echo "--- 3. 检查仿真状态 ---"
echo "执行: ign topic -e -t /world/simple_test_world/stats -n 1"
ign topic -e -t /world/simple_test_world/stats -n 1 2>/dev/null | head -20 || echo "无法获取仿真状态"

echo ""
echo "--- 4. 检查Gazebo日志 ---"
echo "最近的Gazebo日志："
find ~/.gz/log -name "*.log" -type f 2>/dev/null | head -1 | xargs tail -30 2>/dev/null || echo "没有找到日志文件"

echo ""
echo "--- 5. 检查传感器链接详情 ---"
echo "执行: ign model -m scout_mini -l front_lidar_link -s front_lidar_sensor"
ign model -m scout_mini -l front_lidar_link -s front_lidar_sensor 2>/dev/null || echo "传感器信息不可用"

echo ""
echo "--- 6. 测试强制传感器更新 ---"
echo "发送请求以更新传感器..."
for i in {1..5}; do
    echo "尝试 $i..."
    timeout 1 ign topic -e -t /front/scan -n 1 2>&1 | head -5
    sleep 0.5
done

echo ""
echo "--- 7. 检查physics状态 ---"
echo "执行: ign topic -e -t /world/simple_test_world/physics -n 1"
ign topic -e -t /world/simple_test_world/physics -n 1 2>/dev/null | head -15 || echo "无法获取物理状态"

echo ""
echo "========================================"
echo "       诊断完成"
echo "========================================"
echo ""
echo "如果所有命令都没有输出，可能是："
echo "1. Gazebo版本与URDF配置不兼容"
echo "2. sensors-system插件未正确加载"
echo "3. 传感器需要特殊的topic配置"
echo ""
echo "请将输出发送给开发者进行进一步分析。"