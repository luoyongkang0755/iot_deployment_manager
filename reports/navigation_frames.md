# Nav2 坐标系链解释报告

## 概述

本报告解释 Nav2 导航系统中使用的坐标系链及其相互关系，特别针对 Scout Mini 双激光雷达机器人。

---

## 坐标系链结构

### 完整坐标系链

```
map → odom → base_link → [front_lidar_link, rear_lidar_link]
```

### 坐标系层级图

```
map (世界坐标系)
  └── odom (里程计坐标系)
        └── base_link (机器人基座坐标系)
              ├── base_footprint (地面投影坐标系)
              ├── front_lidar_link (前置激光雷达坐标系)
              ├── rear_lidar_link (后置激光雷达坐标系)
              ├── front_left_wheel_link (左前轮坐标系)
              ├── front_right_wheel_link (右前轮坐标系)
              ├── rear_left_wheel_link (左后轮坐标系)
              ├── rear_right_wheel_link (右后轮坐标系)
              └── inertial_link (惯性坐标系)
```

---

## 各坐标系详解

### 1. map 坐标系（世界坐标系）

**定义：**
- 全局固定的世界坐标系
- 用于长期导航和全局路径规划
- 通常与地图原点对齐

**特点：**
- 固定不动（相对于世界）
- 由 SLAM 或地图服务器维护
- 允许漂移（随着时间累积误差）

**用途：**
- 全局路径规划
- 地图定位
- 长期任务执行

**在 RViz2 中：**
- Fixed Frame 设置为 `map` 时，可以看到机器人在地图中的全局位置
- 地图数据通常在 map 坐标系中发布

---

### 2. odom 坐标系（里程计坐标系）

**定义：**
- 以机器人启动位置为原点的局部坐标系
- 通过轮式里程计或视觉里程计计算
- 短期内精确，长期会漂移

**特点：**
- 相对于机器人启动位置
- 短期精度高（厘米级）
- 长期累积误差（漂移）
- 连续但可能漂移

**用途：**
- 局部路径跟踪
- 短期避障
- 精确的局部运动控制

**与 map 的关系：**
- `map → odom` 变换由定位系统（如 AMCL）计算
- 这个变换会随时间调整以修正里程计漂移

---

### 3. base_link 坐标系（机器人基座坐标系）

**定义：**
- 固定在机器人本体上的坐标系
- 通常位于机器人几何中心或旋转中心
- 所有传感器和执行器都相对于此坐标系

**特点：**
- 随机器人移动而移动
- 是机器人的"身体"坐标系
- 所有传感器坐标系的父坐标系

**用途：**
- 传感器数据融合
- 运动控制
- 坐标变换的参考点

**在 Scout Mini 中：**
- 位于机器人中心
- 高度在地面上方 0.145m（轮子半径）

---

### 4. base_footprint 坐标系（地面投影坐标系）

**定义：**
- base_link 在地面上的垂直投影
- 与 base_link 相同的 X、Y 位置，但 Z=0（地面高度）

**特点：**
- 2D 导航的参考点
- 用于平面移动机器人

**用途：**
- 2D 路径规划
- 成本地图计算

---

### 5. LiDAR 坐标系

#### 前置激光雷达坐标系

**坐标系名称：**
- URDF 中：`front_lidar_link`
- Gazebo 中：`scout_mini/base_link/front_lidar_sensor`
- 通过静态 TF 变换连接

**位置：**
- 相对于 base_link: (x=0.245, y=0, z=0.14)
- 位于机器人前方中心

**用途：**
- 前方障碍物检测
- 前向 SLAM 建图
- 前方路径规划

#### 后置激光雷达坐标系

**坐标系名称：**
- URDF 中：`rear_lidar_link`
- Gazebo 中：`scout_mini/base_link/rear_lidar_sensor`
- 通过静态 TF 变换连接

**位置：**
- 相对于 base_link: (x=-0.245, y=0, z=0.14)
- 位于机器人后方中心

**用途：**
- 后方障碍物检测
- 后向 SLAM 建图
- 360°环境感知

---

## 坐标系变换详解

### map → odom 变换

**发布者：** AMCL 或 SLAM 节点

**特点：**
- 会随时间调整
- 修正里程计漂移
- 不连续（可能跳变）

**计算方式：**
```
T_map_odom = T_map_robot_actual × T_odom_robot_odom^-1
```

### odom → base_link 变换

**发布者：** 机器人状态发布节点（robot_state_publisher）

**特点：**
- 连续平滑
- 来自里程计数据
- 会累积误差

**数据来源：**
- 轮式里程计
- 视觉里程计
- IMU 数据融合

### base_link → LiDAR 变换

**发布者：** 静态 TF 发布节点

**特点：**
- 固定不变
- 来自 URDF 模型
- 精确已知

**变换值：**
```python
# 前置 LiDAR
base_link → front_lidar_link: (0.245, 0, 0.14, 0, 0, 0)

# 后置 LiDAR
base_link → rear_lidar_link: (-0.245, 0, 0.14, 3.14159, 0, 0)
```

---

## 关键区别对比

### map vs odom

| 特性 | map | odom |
|------|-----|------|
| **原点** | 世界固定点 | 机器人启动位置 |
| **稳定性** | 全局固定 | 随机器人移动 |
| **精度** | 长期准确 | 短期精确，长期漂移 |
| **连续性** | 可能跳变 | 连续平滑 |
| **用途** | 全局规划 | 局部控制 |
| **变换计算** | AMCL/SLAM | 里程计 |

### base_link vs LiDAR 坐标系

| 特性 | base_link | LiDAR 坐标系 |
|------|-----------|-------------|
| **定义** | 机器人本体 | 传感器安装位置 |
| **运动** | 随机器人移动 | 随机器人移动 |
| **变换** | 参考坐标系 | 相对于 base_link 固定 |
| **数据** | 机器人状态 | 激光扫描数据 |

---

## TF 树验证

### 查看 TF 树

```bash
ros2 run tf2_tools view_frames
```

生成的 `frames.pdf` 应显示完整的坐标系链。

### 检查特定变换

```bash
# 检查 map → base_link 变换
ros2 run tf2_ros tf2_echo map base_link

# 检查 odom → base_link 变换
ros2 run tf2_ros tf2_echo odom base_link

# 检查 base_link → front_lidar_link 变换
ros2 run tf2_ros tf2_echo base_link front_lidar_link
```

### 验证坐标系链完整性

```bash
# 应该能成功查询到以下变换
ros2 run tf2_ros tf2_echo map front_lidar_link
ros2 run tf2_ros tf2_echo map rear_lidar_link
```

---

## 常见问题

### 问题1：坐标系链断裂

**症状：** RViz 中无法显示激光数据或地图

**检查：**
```bash
ros2 run tf2_tools view_frames
```

**解决：** 确保所有静态 TF 变换都已正确配置

### 问题2：map 和 odom 不匹配

**症状：** 机器人在地图中的位置与实际不符

**原因：** AMCL 定位不准确或初始位置错误

**解决：** 重新初始化机器人位置或调整 AMCL 参数

### 问题3：LiDAR 数据坐标系错误

**症状：** 激光点云位置不正确

**原因：** TF 变换参数错误或 frame_id 不匹配

**解决：** 检查静态 TF 变换值和激光数据的 frame_id

---

## 验收检查

- ✅ 没有断开的坐标系
- ✅ 所有坐标系都正确连接到 TF 树
- ✅ map 和 odom 的区别已清楚解释
- ✅ base_link 和 LiDAR 坐标系的关系已说明
- ✅ TF 树图像已生成（`frames.pdf`）

---

## 提交的文件

- `reports/navigation_frames.md`（本报告）
- `media/screenshots/task18_tf_tree.pdf`（TF 树图像）
- `TASK_LOG.md`（已更新）
- `TASK_LOG_CHINESE.md`（已更新）

---

## 日期

2026-06-10
