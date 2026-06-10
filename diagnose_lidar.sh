#!/bin/bash

echo "========================================"
echo "          LiDAR Data Diagnostics"
echo "========================================"

# 1. 检查ROS2环境
echo ""
echo "--- 1. ROS2 Environment Check ---"
echo "ROS_DISTRO: $ROS_DISTRO"
echo "ROS_PACKAGE_PATH: $(echo $ROS_PACKAGE_PATH | head -c 100)..."
echo "PYTHONPATH: $(echo $PYTHONPATH | head -c 100)..."

# 2. 检查话题列表
echo ""
echo "--- 2. ROS2 Topic List ---"
ros2 topic list | grep -E "(scan|lidar)" || echo "No scan/lidar topics found"

# 3. 检查激光雷达话题详情
echo ""
echo "--- 3. Front LiDAR Topic Info ---"
if ros2 topic info /front/scan 2>/dev/null; then
    echo ""
    echo "--- Front LiDAR QoS Profile ---"
    ros2 topic info /front/scan -v | grep -A 10 "QoS profile"
else
    echo "/front/scan topic not found"
fi

echo ""
echo "--- 4. Rear LiDAR Topic Info ---"
if ros2 topic info /rear/scan 2>/dev/null; then
    echo ""
    echo "--- Rear LiDAR QoS Profile ---"
    ros2 topic info /rear/scan -v | grep -A 10 "QoS profile"
else
    echo "/rear/scan topic not found"
fi

# 4. 检查节点状态
echo ""
echo "--- 5. Active Nodes ---"
ros2 node list | grep bridge || echo "No bridge nodes found"

# 5. 检查Gazebo端话题
echo ""
echo "--- 6. Gazebo Topics (gz topic) ---"
if command -v gz &>/dev/null; then
    gz topic -l | grep -i scan 2>/dev/null || echo "No Gazebo scan topics found"
    
    echo ""
    echo "--- Testing Gazebo front/scan topic ---"
    timeout 2 gz topic -e /front/scan --once 2>/dev/null && echo "Gazebo /front/scan has data" || echo "Gazebo /front/scan no data or not found"
    
    echo ""
    echo "--- Testing Gazebo /model/scout_mini/front/scan topic ---"
    timeout 2 gz topic -e /model/scout_mini/front/scan --once 2>/dev/null && echo "Gazebo /model/scout_mini/front/scan has data" || echo "Gazebo /model/scout_mini/front/scan no data or not found"
else
    echo "gz command not available"
fi

# 6. 检查传感器状态
echo ""
echo "--- 7. Gazebo Sensor Status ---"
if command -v gz &>/dev/null; then
    gz sensor -l 2>/dev/null | grep -i lidar || echo "No lidar sensors found in Gazebo"
else
    echo "gz command not available"
fi

# 7. 检查TF树
echo ""
echo "--- 8. TF Tree Check ---"
timeout 2 ros2 run tf2_tools view_frames 2>/dev/null || echo "TF frames check failed"

# 8. 测试实际数据接收
echo ""
echo "--- 9. Testing Data Reception ---"
echo "Testing /front/scan with default QoS..."
timeout 3 ros2 topic echo /front/scan --once 2>&1 | head -5 || echo "No data received"

echo ""
echo "Testing /front/scan with sensor_data QoS..."
timeout 3 ros2 topic echo /front/scan --qos-profile sensor_data --once 2>&1 | head -5 || echo "No data received with sensor_data QoS"

echo ""
echo "========================================"
echo "          Diagnostics Complete"
echo "========================================"