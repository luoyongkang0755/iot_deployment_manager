# 双 LiDAR 验证报告

## 概述

本报告验证 Scout Mini 双激光雷达系统的正常工作状态，包括前置和后置 LiDAR 传感器的数据发布、坐标系变换以及 RViz2 可视化。

---

## 验证环境

| 项目 | 说明 |
|------|------|
| 系统 | ROS2 Humble |
| 仿真环境 | Gazebo Sim (Ignition) |
| 机器人模型 | Scout Mini Dual LiDAR |

---

## 前置 LiDAR 验证

### 话题信息

| 项目 | 值 |
|------|-----|
| **话题名称** | `/front/scan` |
| **消息类型** | `sensor_msgs/msg/LaserScan` |

### 坐标系信息

| 项目 | 值 |
|------|-----|
| **传感器坐标系** | `scout_mini/base_link/front_lidar_sensor` |
| **父坐标系** | `front_lidar_link` |
| **变换关系** | `front_lidar_link` → `scout_mini/base_link/front_lidar_sensor` |
| **位置 (xyz)** | `0.245, 0, 0.14` |
| **姿态 (rpy)** | `0, 0, 0` |

---

## 后置 LiDAR 验证

### 话题信息

| 项目 | 值 |
|------|-----|
| **话题名称** | `/rear/scan` |
| **消息类型** | `sensor_msgs/msg/LaserScan` |

### 坐标系信息

| 项目 | 值 |
|------|-----|
| **传感器坐标系** | `scout_mini/base_link/rear_lidar_sensor` |
| **父坐标系** | `rear_lidar_link` |
| **变换关系** | `rear_lidar_link` → `scout_mini/base_link/rear_lidar_sensor` |
| **位置 (xyz)** | `-0.245, 0, 0.14` |
| **姿态 (rpy)** | `0, 0, 0` |

---

## 数据频率验证

### 终端输出结果

```bash
# 前置 LiDAR 频率
$ ros2 topic hz /front/scan
average rate: 9.894
	min: 0.096s max: 0.104s std dev: 0.00230s window: 11

# 后置 LiDAR 频率
$ ros2 topic hz /rear/scan
average rate: 9.876
	min: 0.096s max: 0.105s std dev: 0.00197s window: 21
```

### 频率统计

| 传感器 | 平均频率 | 最小间隔 | 最大间隔 | 标准差 |
|--------|----------|----------|----------|--------|
| 前置 LiDAR | ~10 Hz | 0.096s | 0.104s | 0.0023s |
| 后置 LiDAR | ~10 Hz | 0.096s | 0.105s | 0.00197s |

---

## 坐标系变换验证

### TF 树结构

```
base_link
  ├── front_lidar_link
  │     └── scout_mini/base_link/front_lidar_sensor (前置传感器)
  ├── rear_lidar_link
  │     └── scout_mini/base_link/rear_lidar_sensor (后置传感器)
  ├── front_left_wheel_link
  ├── front_right_wheel_link
  ├── rear_left_wheel_link
  ├── rear_right_wheel_link
  ├── inertial_link
  └── base_footprint
```

### 静态 TF 变换配置

| 变换 | 父帧 | 子帧 | 位置 | 姿态 |
|------|------|------|------|------|
| 前置 LiDAR | `front_lidar_link` | `scout_mini/base_link/front_lidar_sensor` | (0.245, 0, 0.14) | (0, 0, 0) |
| 后置 LiDAR | `rear_lidar_link` | `scout_mini/base_link/rear_lidar_sensor` | (-0.245, 0, 0.14) | (0, 0, 0) |

---

## RViz2 可视化验证

### 配置信息

| 项目 | 设置 |
|------|------|
| Fixed Frame | `base_link` |
| LaserScan 话题 | `/front/scan` 和 `/rear/scan` |
| 显示样式 | Points |
| 点大小 | 0.1m |
| Queue Size | 10 |

### 截图路径

```
media/screenshots/task15.png
```

### 可视化结果

✅ **前置 LiDAR**: 激光点云正确显示在机器人前方
✅ **后置 LiDAR**: 激光点云正确显示在机器人后方
✅ **坐标系**: 两个传感器坐标系都正确连接到 `base_link`

---

## 验证结论

### 验收检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 前置 LiDAR 发布数据 | ✅ 通过 | `/front/scan` 话题正常发布 LaserScan 消息 |
| 后置 LiDAR 发布数据 | ✅ 通过 | `/rear/scan` 话题正常发布 LaserScan 消息 |
| 前置坐标系连接 | ✅ 通过 | `scout_mini/base_link/front_lidar_sensor` → `front_lidar_link` → `base_link` |
| 后置坐标系连接 | ✅ 通过 | `scout_mini/base_link/rear_lidar_sensor` → `rear_lidar_link` → `base_link` |
| RViz2 可视化前置扫描 | ✅ 通过 | 激光点云正确显示 |
| RViz2 可视化后置扫描 | ✅ 通过 | 激光点云正确显示 |

### 最终结论

✅ **双 LiDAR 系统验证通过**

两个 LiDAR 传感器均正常工作，数据发布频率稳定在约 10Hz，坐标系变换正确，RViz2 可以正确可视化两个激光扫描数据。

---

## 修改的文件

| 文件路径 | 修改内容 |
|----------|----------|
| `src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py` | 添加静态 TF 变换节点 |
| `src/external/scout_ros2/scout_description/urdf/scout_mini.xacro` | 传感器类型从 `ray` 改为 `gpu_ray` |

---

## 日期

2026-06-10
