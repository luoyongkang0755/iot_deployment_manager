# SLAM 建图说明

## 概述

本项目使用 SLAM Toolbox 进行激光SLAM建图，支持 Scout Mini 双激光雷达机器人。

## 建图步骤

### 1. 启动SLAM建图环境

```bash
# 构建项目
colcon build --symlink-install

# 启动SLAM建图
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py
```

### 2. 控制机器人移动

在另一个终端中使用键盘控制机器人：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 3. 保存地图

当建图完成后，在另一个终端中保存地图：

```bash
# 保存地图到maps目录
ros2 run nav2_map_server map_saver_cli -f maps/nav2_test_map
```

### 4. 验证地图

```bash
# 检查map话题
ros2 topic list | grep map

# 查看地图信息
ros2 topic info /map
```

## 文件说明

### 启动文件
- `launch/slam.launch.py` - SLAM建图启动文件

### 参数配置
- `params/slam_toolbox_params.yaml` - SLAM Toolbox 参数配置

### 地图文件
- `maps/nav2_test_map.yaml` - 地图元数据
- `maps/nav2_test_map.pgm` - 地图图像

## 建图最佳实践

1. **初始位置**: 机器人从原点(0,0)开始
2. **移动策略**: 
   - 缓慢移动，避免快速旋转
   - 覆盖所有需要建图的区域
   - 经过同一位置多次以优化地图
3. **地图分辨率**: 0.05m/pixel
4. **保存时机**: 当地图不再明显变化时保存

## 依赖安装

```bash
# 安装SLAM Toolbox
sudo apt install ros-humble-slam-toolbox

# 安装导航相关包
sudo apt install ros-humble-nav2-map-server
```

## 故障排除

### 问题1: 无法看到地图
- 确保 `/map` 话题有数据
- 检查 RViz 的 Fixed Frame 设置为 `map`
- 确认 SLAM Toolbox 节点正常运行

### 问题2: 地图保存失败
- 确保 `maps/` 目录存在且有写入权限
- 检查 map_saver_cli 命令的路径参数

### 问题3: 激光数据不更新
- 检查 `/front/scan` 话题是否有数据
- 确认 QoS 配置正确

## 示例命令

```bash
# 启动SLAM建图
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py

# 键盘控制
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 保存地图
ros2 run nav2_map_server map_saver_cli -f maps/nav2_test_map

# 查看地图服务
ros2 service list | grep map
```