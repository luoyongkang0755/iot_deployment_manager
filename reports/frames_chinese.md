# Nav2 坐标系链解释报告

## 概述

本报告解释 Nav2 导航系统中使用的坐标系链及其相互关系，特别针对 Scout Mini 双激光雷达机器人。Task 18 更新反映了解决 Gazebo 模型名前缀问题后的实际 TF 树结构。

---

## 实际 TF 树结构（Task 18 验证）

TF 树已通过 `ros2 run tf2_tools view_frames` 验证。实际链在 Gazebo 命名空间帧与 ROS 标准帧之间插入了**模型前缀桥接帧**：

```
地图定位   SLAM 发布              map → odom
          （由 AMCL 或 SLAM Toolbox 更新）

前缀桥接   静态身份 TF             odom → scout_mini/odom
          （Task 17 添加）         scout_mini/base_link → base_link

Gazebo    差速驱动插件            scout_mini/odom → scout_mini/base_link
里程计     （带 "scout_mini/" 前缀）

URDF      robot_state_publisher   base_link → [front_lidar_link, rear_lidar_link,
静态变换                             base_footprint, inertial_link,
                                    front_left_wheel_link, ...]
```

### 完整坐标系链

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → front_lidar_link
        ↓                              ↑
  （diff drive 发布）         （静态 TF 身份桥接）
```

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → rear_lidar_link
```

### 为什么需要前缀桥接

Ignition Gazebo 差速驱动插件会自动在所有发布的 frame ID 前添加模型名（`scout_mini/`）前缀。这导致形成了两个不相连的 TF 子树：

- **子树 A**（来自 Gazebo bridge）：`scout_mini/odom → scout_mini/base_link`（50 Hz）
- **子树 B**（来自 robot_state_publisher）：`base_link → front_lidar_link, rear_lidar_link, ...`

如果不桥接，SLAM Toolbox 找不到 `odom → base_link`，因为 `odom` 和 `base_link`（不带前缀）分别位于两个独立的子树中——TF 链断裂。

**解决方案**（已在 [scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py) 中实现）：

```python
# 连接标准 ROS odom 到 Gazebo 的 scout_mini/odom（身份变换）
static_transform_publisher 0 0 0 0 0 0 odom scout_mini/odom

# 连接 Gazebo 的 scout_mini/base_link 到 ROS 的 base_link（身份变换）
static_transform_publisher 0 0 0 0 0 0 scout_mini/base_link base_link
```

### 坐标系层级图（实际）

```
map                          （SLAM / AMCL 发布）
  └── odom                   （ROS 标准帧：身份桥接目标）
        └── scout_mini/odom  （Gazebo 里程计帧，带模型名前缀）
              └── scout_mini/base_link  （Gazebo 基座帧，带模型名前缀）
                    └── base_link       （ROS 标准帧：身份桥接源）
                          ├── base_footprint          （地面投影）
                          ├── front_lidar_link        （前 RS-AIRY 激光雷达）
                          ├── rear_lidar_link         （后 RS-AIRY 激光雷达）
                          ├── front_left_wheel_link   （左前轮）
                          ├── front_right_wheel_link  （右前轮）
                          ├── rear_left_wheel_link    （左后轮）
                          ├── rear_right_wheel_link   （右后轮）
                          └── inertial_link           （惯导 / 惯性）
```

**Gazebo 传感器帧**（内部）：
```
scout_mini/base_link/front_lidar_sensor  →  父帧: front_lidar_link
scout_mini/base_link/rear_lidar_sensor   →  父帧: rear_lidar_link
```
这些由 `robot_state_publisher` 发布，仅供 Gazebo 传感器内部使用；RViz 中不需要直接用到。

---

## 各坐标系详解

### 1. map 坐标系（世界坐标系）

**定义：**
- 全局固定的世界坐标系，对齐地图原点
- 用于长期导航和全局路径规划

**特点：**
- 固定不动（相对于世界）
- 由 SLAM Toolbox（建图模式）或 AMCL（定位模式）维护
- 不连续 — 重新定位时可能跳变

**发布者：** SLAM Toolbox 节点或 AMCL 节点
**变换类型：** 动态（定期更新）

**用途：**
- 全局路径规划（Nav2 PlannerServer）
- RViz 地图可视化
- 长期任务执行

**SLAM Toolbox 配置**（[slam_toolbox_params.yaml](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/params/slam_toolbox_params.yaml#L15)）：
```yaml
map_frame: map
```

---

### 2. odom 坐标系（里程计坐标系）

**定义：**
- 以机器人启动位置为原点的局部坐标系
- 表示由轮式里程计估算的机器人运动
- 短期内精确，长期因积分误差而漂移

**特点：**
- 连续平滑 — 不会跳变
- 短期精度高（厘米级）
- 长期漂移无界

**发布者：** Gazebo 差速驱动插件（通过 `ros_gz_bridge` 桥接到 ROS）
**变换类型：** 平滑连续，以 50 Hz 更新

**差速驱动插件配置**（[scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L157)）：
```xml
<odom_frame>odom</odom_frame>
<robot_base_frame>base_footprint</robot_base_frame>
<odom_publish_frequency>50</odom_publish_frequency>
```

**用途：**
- 局部路径跟踪（Nav2 ControllerServer）
- 短期避障
- `map → odom` 变换由 SLAM/AMCL 发布以修正漂移

---

### 3. scout_mini/odom 和 scout_mini/base_link（Gazebo 前缀帧）

**背景：**
Ignition Gazebo 自动在所有模型插件发布的 frame ID 前添加 `{模型名}/` 前缀。对于名为 `scout_mini` 的模型，差速驱动插件发布：
- `scout_mini/odom → scout_mini/base_link`

**桥接帧**（身份变换）：
- `odom → scout_mini/odom` — 连接 ROS 标准帧至 Gazebo 命名空间帧
- `scout_mini/base_link → base_link` — 连接 Gazebo 命名空间帧至 ROS 标准帧

两者均为**零偏移**（身份）变换：translation = (0,0,0), rotation = (0,0,0)。

**发布者：** launch 文件中的 static_transform_publisher
**变换类型：** 静态（永不改变）

这些帧仅用于连接两种命名约定；不代表任何物理偏移。

---

### 4. base_link 坐标系（机器人基座坐标系）

**定义：**
- 固定在机器人本体几何中心的坐标系
- 所有传感器和 URDF 静态变换相对此坐标系

**特点：**
- 随机器人移动
- 是机器人的"身体"坐标系
- URDF 中所有传感器/轮子帧的父帧

**在 Scout Mini 上的位置：**
- 机器人本体中心（前距 base_x_size/2，侧距 base_y_size/2）
- 高度：wheel_radius (0.145m) 离地（z 偏移来自地面 base_footprint）

**用途：**
- 传感器数据融合参考
- 运动控制目标
- URDF 变换树的根

**SLAM Toolbox 配置：**
```yaml
base_frame: base_link
```

---

### 5. base_footprint 坐标系（地面投影坐标系）

**定义：**
- base_link 在地面上的垂直投影（z = -wheel_radius 相对 base_link）
- 与 base_link 相同 X/Y 位置，Z = 0 位于地面高度

**URDF 定义**（[scout_mini.xacro](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/urdf/scout_mini.xacro#L52-L56)）：
```xml
<joint name="base_footprint_joint" type="fixed">
    <origin xyz="0 0 ${-wheel_radius}" rpy="0 0 0" />
    <parent link="base_link" />
    <child link="base_footprint" />
</joint>
```
其中 `wheel_radius = 0.145m`，因此 `base_footprint` 位于 `base_link` 下方 0.145m。

**用途：**
- 2D 导航和代价地图参考点
- Nav2 足迹模型使用

---

### 6. LiDAR 坐标系

#### 前置激光雷达（RS-AIRY）

**帧名：** `front_lidar_link`

**相对 base_link 的位置**（[scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L111)）：
```xml
<origin xyz="${base_x_size/2 - 0.08} 0.0 ${base_z_size/2 + 0.05}" rpy="0 0 0" />
<!-- = (0.245, 0, 0.14) --!>
```
- 从中心向前 0.245m
- 从 base_link 中心向上 0.14m

**传感器话题：** `/front/scan`（5 Hz 发布）
**360°** 水平扫描（samples=360，分辨率=1°）

#### 后置激光雷达（RS-AIRY）

**帧名：** `rear_lidar_link`

**相对 base_link 的位置**（[scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro#L141)）：
```xml
<origin xyz="${-base_x_size/2 + 0.08} 0.0 ${base_z_size/2 + 0.05}" rpy="0 0 3.14159" />
<!-- = (-0.245, 0, 0.14)，偏航 180° 旋转 --!>
```
- 从中心向后 0.245m
- 从 base_link 中心向上 0.14m
- 偏航 180° 旋转（朝向后方）

**传感器话题：** `/rear/scan`（5 Hz 发布）
**360°** 水平扫描

---

## 关键区别对比

### map vs odom

| 特性 | map | odom |
|------|-----|------|
| **原点** | 世界固定点（地图原点） | 机器人启动位置 |
| **稳定性** | 全局固定，可能跳变 | 随机器人移动，始终平滑 |
| **精度** | 长期准确（有回环闭合） | 短期精确，长期无界漂移 |
| **连续性** | 不连续（重定位时跳变） | 连续且平滑 |
| **发布者** | SLAM Toolbox / AMCL | Gazebo diff drive → ros_gz_bridge |
| **更新频率** | ~2–10 Hz（依赖 SLAM） | 50 Hz（odom_publish_frequency） |
| **用途** | 全局路径规划、地图任务 | 局部运动控制、避障 |
| **误差累积** | 由回环闭合/地图匹配约束 | 无界累积漂移 |

**为什么两者都需要：**
- `odom` 提供平滑、高频的状态用于实时控制
- `map` 提供基于已知地标的全局修正定位
- `map → odom` 变换桥接漂移：SLAM 修正全局位置时调整 `map → odom` 偏移量，使得机器人最新的 `odom → base_link` 仍能指向正确的 `map` 位置

### base_link vs LiDAR 坐标系

| 特性 | base_link | front_lidar_link | rear_lidar_link |
|------|-----------|-----------------|-----------------|
| **位置（相对 base_link）** | — | (0.245, 0, 0.14) | (-0.245, 0, 0.14) |
| **朝向** | 前方 (0°) | 前方 (0°) | 后方 (180°) |
| **发布数据** | 机器人位姿（来自里程计） | /front/scan | /rear/scan |
| **变换类型** | 参考坐标系 | 静态（URDF 定义） | 静态（URDF 定义） |
| **被谁使用** | Nav2 规划器、控制器 | SLAM（主扫描源） | 障碍物检测（若合并） |

---

## 坐标系变换详解

### map → odom（定位修正）

**发布者：** SLAM Toolbox（建图模式）或 AMCL（定位模式）

**行为：**
- SLAM/AMCL 修正机器人全局位置时更新
- 可能离散"跳变"（变换值阶跃变化）
- 初始建图时：SLAM Toolbox 在原点设置 `map = odom`，然后随建图更新

**检查：**
```bash
ros2 run tf2_ros tf2_echo map odom
```

### odom → base_link（里程计运动）

**发布者：** Gazebo diff drive 插件 → ros_gz_bridge → /tf topic

**行为：**
- 连续平滑，以 50 Hz 更新
- 来自 Gazebo 中的轮式编码器仿真
- 起点附近较精确，长时间运行漂移增大

**桥接配置**（[scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py)）：
```
/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V
```

### base_link → LiDAR（静态 URDF 变换）

**发布者：** robot_state_publisher

**行为：**
- 永久不变的变换
- 由 URDF 模型的 `<joint>` 元素定义
- 两个雷达均固定在机器人本体上（无活动关节）

**检查：**
```bash
ros2 run tf2_ros tf2_echo base_link front_lidar_link
ros2 run tf2_ros tf2_echo base_link rear_lidar_link
```

---

## TF 树验证命令

### 查看完整 TF 树
```bash
ros2 run tf2_tools view_frames
```
生成的 `frames.pdf` 显示所有连接的坐标系。

### 检查特定变换
```bash
# 定位链（漂移修正）
ros2 run tf2_ros tf2_echo map odom

# 里程计链（高频运动）
ros2 run tf2_ros tf2_echo odom base_link

# LiDAR 变换（静态，URDF 定义）
ros2 run tf2_ros tf2_echo base_link front_lidar_link
ros2 run tf2_ros tf2_echo base_link rear_lidar_link
```

### 验证端到端链完整性
```bash
ros2 run tf2_ros tf2_echo map front_lidar_link     # 应成功
ros2 run tf2_ros tf2_echo map rear_lidar_link      # 应成功
ros2 run tf2_ros tf2_echo odom front_lidar_link    # 应成功
```

### 检查 Gazebo 内部帧（调试用）
```bash
ign topic -l | grep tf     # 列出 Gazebo TF 相关话题
ign topic -i -t /tf        # 显示 Gazebo /tf 消息类型
```

---

## 常见问题与解决方案

### 问题1：坐标系链断裂

**症状：**
- RViz 中无法显示 LaserScan 或 Map
- `ros2 topic echo /map --once` 无输出
- `ros2 run tf2_ros tf2_echo map base_link` 失败

**根因（本项目）：**
Gazebo diff drive 插件发布 `scout_mini/odom → scout_mini/base_link`（带模型名前缀），而 `robot_state_publisher` 使用 `base_link`（无前缀）。两个不相连的 TF 子树。

**解决：**
添加静态身份 TF 变换：`odom → scout_mini/odom` 和 `scout_mini/base_link → base_link`。

**检查：**
```bash
ros2 run tf2_tools view_frames
# 必须显示从 map 到所有叶子帧的单一连通的树
```

### 问题2：map 和 odom 不匹配

**症状：** 机器人在 RViz 地图中的位置不正确。

**原因：** AMCL 定位不准确，或 SLAM 尚未建立 `map → odom`。

**解决：**
- 建图时：确保 `mode: mapping`，让机器人走闭环路径进行回环闭合
- 定位时：通过 RViz 的"2D Pose Estimate"工具提供准确的初始位姿估计

### 问题3：LiDAR 数据位置不正确

**症状：** 激光点云在 RViz 中相对机器人模型偏移。

**原因：** `front_lidar_link` 或 `rear_lidar_link` 的静态变换值有误。

**检查 URDF 关节位置：**
```bash
ros2 run tf2_ros tf2_echo base_link front_lidar_link
# 应输出 translation: (0.245, 0, 0.14)
```

---

## 验收检查

- ✅ 没有断开的坐标系 — 所有帧连接在单个 TF 树中
- ✅ `map → odom` 的区别已清楚解释（离散 vs 连续）
- ✅ `base_link` 与 LiDAR 坐标系的关系已说明（来自 URDF 的静态变换）
- ✅ 模型名前缀桥接机制已文档化
- ✅ 通过 `ros2 run tf2_tools view_frames` 生成 TF 树图像
- ✅ 所有端到端变换可验证（`map → front_lidar_link` 正常）

---

## 提交的文件

- `reports/navigation_frames.md`（本报告，Task 18 更新）
- `reports/frames_chinese.md`（中文版，Task 18 更新）
- `TASK_LOG.md`（已更新）
- `TASK_LOG_CHINESE.md`（已更新）

---

## 日期

2026-06-12（Task 18 — 根据已验证的 Gazebo + SLAM 流水线，更新为实际 TF 树结构）
