# 最终技术报告 — Scout Mini 双激光雷达导航系统

**作者**: 学生  
**日期**: 2026-07-14  
**仓库**: [scout_mini_nav2](https://github.com/luoyongkang0755/scout_mini_nav2)  
**ROS 2 发行版**: Humble  

---

## 1. 引言

本报告记录了 AgileX Scout Mini 机器人自主导航系统的设计、实现和测试过程。系统使用 ROS2 Humble 框架、Nav2 导航栈以及 Gazebo Ignition (Fortress) 仿真。两个 RS-AIRY 激光雷达传感器（前、后）被仿真以提供 360° 感知覆盖。

该项目以结构化作业形式完成，包含 28 个任务，覆盖从基础 Linux 命令到完全可复现、文档完备的导航系统的全部阶段，并实现了仿真与真实机器人配置的分离。

---

## 2. 作业目标

| 目标 | 状态 |
|------|------|
| ROS2 工作空间与包创建 | 已完成 |
| 发布者/订阅者通信 | 已完成 |
| TF 树与坐标系理解 | 已完成 |
| Docker 容器化 ROS2 环境（含 GUI） | 已完成 |
| Scout Mini URDF 模型（RViz2 与 Gazebo） | 已完成 |
| 双 RS-AIRY 激光雷达仿真 | 已完成 |
| 遥控与传感器验证 | 已完成 |
| 带障碍物的导航世界 | 已完成 |
| SLAM 建图与地图准备 | 已完成 |
| Nav2 集成（AMCL、规划器、控制器、行为树） | 已完成 |
| 三目标点导航测试（100% 成功率） | 已完成 |
| 干净构建可复现性（零错误） | 已完成 |
| 仿真与真实机器人配置分离 | 已完成 |
| 真实机器人安全检查表 | 已完成 |
| 面向可复现性的完整 README | 已完成 |

---

## 3. 仓库结构

```
scout_nav2_mini/
├── src/
│   ├── scout_mini_dual_lidar_gazebo/          # 主 Nav2 + Gazebo 包
│   │   ├── config/
│   │   │   ├── nav2_params.yaml               # Nav2 参数（所有节点）
│   │   │   ├── navigate_no_init_check.xml     # 自定义行为树
│   │   │   ├── simulation/nav2_params.yaml    # 仿真专用配置
│   │   │   └── real_robot/nav2_params.yaml    # 真实机器人配置
│   │   ├── launch/
│   │   │   ├── nav2_launch.py                 # 一键全栈启动
│   │   │   ├── scout_mini_gazebo.launch.py    # 仅 Gazebo
│   │   │   ├── slam.launch.py                 # SLAM Toolbox
│   │   │   ├── simulation/                    # 仿真启动文件
│   │   │   └── real_robot/                    # 真实机器人启动文件
│   │   ├── maps/                              # 预建 SLAM 地图
│   │   ├── worlds/                            # Gazebo 世界文件
│   │   └── src/                               # Python 节点（7 个脚本）
│   ├── external/scout_ros2/                   # AgileX Scout ROS2 包
│   │   ├── scout_description/                 # URDF/XACRO 模型
│   │   ├── scout_msgs/                        # 自定义 ROS 消息
│   │   └── scout_base/                        # CAN 驱动（真实机器人）
│   └── ros2_learning_examples/                # 基础发布/订阅示例
├── docker/                                    # Dockerfile + 运行脚本
├── reports/                                   # 所有任务报告
├── media/                                     # 截图、视频、日志
├── README.md                                  # 完整配置指南
└── TASK_LOG.md                                # 逐任务日志
```

---

## 4. Docker 环境

基于 `ros:humble-ros-base` 构建了自定义 Docker 镜像，提供完全容器化的开发环境。Dockerfile 包含：

- **ROS2 Humble 基础**及构建工具（colcon、cmake）
- **Nav2** 全栈（`nav2-bringup`、`nav2-amcl`、`nav2-planner`、`nav2-controller` 等）
- **Gazebo Ignition**（`ros-gz-sim`、`ros-gz-bridge`）
- **SLAM Toolbox** 用于建图
- **RViz2** + **teleop_twist_keyboard** 用于交互
- **清华镜像源** 加速 apt/rosdep

**构建和运行命令：**

```bash
docker build -t ros2_humble_minimal:latest -f docker/Dockerfile .
bash docker/run.sh
```

容器使用 `--net=host` 和 X11 转发以支持 GUI（Gazebo + RViz2）。入口脚本自动加载 ROS2 和工作空间环境。

---

## 5. Scout Mini 仿真

### URDF 模型

Scout Mini 使用 Xacro 格式建模，具有以下参数：
- **尺寸**: 600mm × 370mm × 285mm（长×宽×高）
- **轮子**: 4 轮（145mm 半径），差速驱动
- **质量**: ~22 kg
- **Gazebo 插件**: DiffDrive（运动控制）、IMU 传感器、关节状态发布

模型通过 `robot_state_publisher` 发布 `/robot_description` 和静态坐标变换。

### Gazebo 生成

机器人在位置 `(0, 0, 0.181)` 处以可配置的偏航角生成，世界为 16m×16m 封闭空间，包含 6 个彩色障碍物箱和边界墙。

| 障碍物 | 位置 (x,y) | 尺寸 (m) | 颜色 |
|--------|------------|----------|------|
| 箱子 1 | (4.0, 0.0) | 1.0×1.0×1.0 | 红色 |
| 箱子 2 | (0.0, 4.0) | 0.8×0.8×0.6 | 绿色 |
| 箱子 3 | (0.0, -4.0) | 1.2×0.6×0.8 | 蓝色 |
| 箱子 4 | (-4.0, 0.0) | 0.8×1.5×1.2 | 黄色 |
| 箱子 5 | (3.0, 3.0) | 0.7×0.7×0.8 | 紫色 |
| 箱子 6 | (-3.0, -3.0) | 0.9×0.9×1.0 | 橙色 |

![Gazebo 世界](media/screenshots/task16_gazebo.png)

---

## 6. 双 RS-AIRY 激光雷达仿真

两个 RS-AIRY 激光雷达传感器已集成到 Scout Mini URDF 中：

| 传感器 | 位置 (x,y,z) | 话题 | 坐标系 |
|--------|---------------|------|--------|
| 前雷达 | (0.245, 0, 0.14) | `/front/scan` | `front_lidar_link` |
| 后雷达 | (-0.245, 0, 0.14) | `/rear/scan` | `rear_lidar_link` |

### 雷达规格
- **量程**: 0.1m – 25m
- **角度分辨率**: 1°（360 个采样点）
- **更新频率**: ~10 Hz

### 传感器处理流水线

由于 Gazebo 会在 frame_id 前加上模型名称前缀，需实现以下处理流水线：

```
Gazebo 雷达 → ros_gz_bridge → scan_frame_fixer.py → laser_merger.py → /merged/scan
```

1. **`scan_frame_fixer.py`**: 去除 frame_id 中的 `scout_mini/` 前缀
2. **`laser_merger.py`**: 将前后雷达数据合并为单一 360° `/merged/scan` 话题

### 频率验证

```
$ ros2 topic hz /front/scan
average rate: 9.894 Hz

$ ros2 topic hz /rear/scan
average rate: 9.876 Hz
```

![RViz2 中的双雷达](media/screenshots/task15.png)

---

## 7. TF 树与 ROS 话题

### TF 树结构

```
map
 └── odom
      └── base_link
           ├── front_lidar_link
           └── rear_lidar_link
```

- `map → odom`: 由 AMCL 定位提供（修正里程计漂移）
- `odom → base_link`: 来自 Gazebo DiffDrive 的实时里程计（通过 `odom_to_tf.py`）
- `base_link → front_lidar_link` / `rear_lidar_link`: 来自 URDF 的静态坐标变换

![TF 树](media/screenshots/task18_tf.png)

### 关键 ROS 话题

| 话题 | 类型 | 发布者 | 功能 |
|------|------|--------|------|
| `/front/scan` | LaserScan | ros_gz_bridge | 前雷达数据 |
| `/rear/scan` | LaserScan | ros_gz_bridge | 后雷达数据 |
| `/merged/scan` | LaserScan | laser_merger | 融合 360° 扫描 |
| `/cmd_vel` | Twist | teleop / Nav2 | 速度指令 |
| `/odom` | Odometry | odom_to_tf | 修正后的里程计 |
| `/map` | OccupancyGrid | map_server | 静态环境地图 |
| `/plan` | Path | planner_server | 全局路径 |
| `/local_plan` | Path | controller_server | 局部轨迹 |
| `/amcl_pose` | PoseWithCovariance | AMCL | 定位后的机器人位姿 |
| `/tf` | TFMessage | robot_state_publisher, AMCL, odom_to_tf | 坐标变换 |

---

## 8. 地图准备

使用预建的 SLAM 地图（`my_map.yaml` / `my_map.pgm`）进行定位和导航。地图通过在 Gazebo 世界中驱动机器人并运行 SLAM Toolbox 生成，然后用 `map_saver_cli` 保存。

**地图属性：**

| 属性 | 值 |
|------|-----|
| 格式 | PGM（便携式灰度图） |
| 分辨率 | 0.05 m/pixel |
| 尺寸 | ~16m × 16m |
| 原点 | (-8.38, -8.01) |
| 占用阈值 | 0.65 |
| 空闲阈值 | 0.25 |

**SLAM 工作流程：**

```bash
# 启动 Gazebo
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 启动 SLAM
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py

# 驱动机器人探索环境
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 保存地图
ros2 run nav2_map_server map_saver_cli -f ~/my_map
```

---

## 9. Nav2 配置

### 部署的节点

| 节点 | 包 | 功能 |
|------|-----|------|
| `map_server` | nav2_map_server | 提供静态占用栅格地图 |
| `amcl` | nav2_amcl | 自适应蒙特卡洛定位 |
| `planner_server` | nav2_planner | 全局路径规划（NavFn/A*） |
| `controller_server` | nav2_controller | 局部路径跟随（DWB） |
| `bt_navigator` | nav2_bt_navigator | 行为树引擎 |
| `recoveries_server` | nav2_behaviors | 旋转/后退/等待恢复行为 |
| `waypoint_follower` | nav2_waypoint_follower | 航点序列执行 |
| `lifecycle_manager` | nav2_lifecycle_manager | 自动激活所有节点 |

### 全局规划器: NavFn

- 基于栅格的 A* 搜索
- 容差: 0.5m
- 允许穿越未知区域

### 局部控制器: DWB（动态窗口法）

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_vel_x` | 0.5 m/s | 前进速度限制 |
| `max_vel_theta` | 1.0 rad/s | 旋转速度限制 |
| `min_vel_x` | 0.0 m/s | 允许目标附近纯旋转 |
| `min_speed_xy` | 0.0 | 启用零线速度轨迹 |
| `xy_goal_tolerance` | 0.25 m | 位置容差 |
| `yaw_goal_tolerance` | 0.5 rad | 朝向容差 |
| `sim_time` | 1.7 s | 轨迹仿真前瞻时间 |
| `vx_samples` | 20 | 线速度采样数 |
| `vtheta_samples` | 20 | 角速度采样数 |

**评分器（critics）：**
- `RotateToGoal`（旋转至目标）、`Oscillation`（震荡）、`BaseObstacle`（基础障碍物）
- `GoalAlign`（目标对齐）、`PathAlign`（路径对齐）、`PathDist`（路径距离）、`GoalDist`（目标距离）

### 行为树

创建了自定义行为树文件（`navigate_no_init_check.xml`），绕过了 `InitialPoseReceived` 条件检查（该变量在当前 Nav2 版本中不会自动设置）。行为树包含正确的黑板端口绑定，确保 `goal` 和 `path` 数据在节点间正常传递。

### 代价地图配置

| 层级 | 局部 | 全局 |
|------|------|------|
| 尺寸 | 3m × 3m 滚动窗口 | 静态地图边界 |
| 分辨率 | 0.05 m/pixel | 0.05 m/pixel |
| 机器人半径 | 0.3 m | 0.3 m |
| 膨胀半径 | 0.55 m | 0.55 m |
| 更新频率 | 5 Hz | 1 Hz |

---

## 10. 导航测试结果

### 三目标点测试

使用脚本通过 `/navigate_to_pose` action 服务器依次发送三个导航目标进行系统验证。

**最终测试结果：**

| 测试 | 起始位姿 | 目标位姿 | 结果 | 时间 | 碰撞 | 备注 |
|------|----------|----------|------|------|------|------|
| 1 | (0,0,0) | (2.0, 0.0, 0.0) | **成功** | ~4s | 无 | 直线路径 |
| 2 | (0,0,0) | (-2.0, 2.0, 0.0) | **成功** | ~15s | 无 | 对角线带避障 |
| 3 | (0,0,0) | (2.0, -2.0, 0.0) | **成功** | ~14s | 无 | 对角线带目标旋转 |

**成功率: 100%（3/3）**

![目标 1 — RViz2](media/screenshots/task%2022%20goal%201.png)
![目标 2 — RViz2](media/screenshots/task22%20goal2.png)
![目标 3 — RViz2](media/screenshots/task22%20goal3.png)

**视频**: [media/task22 vedio.webm](media/task22%20vedio.webm)

### Nav2 终端日志（节选）

```
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
[bt_navigator] Begin navigating from current location (1.77, -0.02) to (-2.00, 2.00)
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
[bt_navigator] Begin navigating from current location (-1.94, 1.95) to (2.00, -2.00)
[controller_server] Reached the goal!
[bt_navigator] Goal succeeded
```

完整日志: [media/LOG/task22.log](media/LOG/task22.log)

---

## 11. 问题与修复

### 问题 1: 行为树卡在 InitialPoseReceived 条件

**症状**: 机器人接受目标但从未开始路径规划。行为树卡在 `InitialPoseReceived` 条件节点。

**根因**: `initial_pose_received` 黑板变量在较新版本的 Nav2 中不会自动设置。

**修复**: 创建 `navigate_no_init_check.xml`，移除 `InitialPoseReceived` 检查，使 `ComputePathToPose` 直接执行。

### 问题 2: 缺少黑板端口绑定

**症状**: `ComputePathToPose` 和 `FollowPath` 节点无法共享 `goal` 和 `path` 数据。

**修复**: 添加显式端口绑定: `goal="{goal}"`、`path="{path}"`、`planner_id="GridBased"`、`controller_id="FollowPath"`。

### 问题 3: 目标附近震荡与超时

**症状**: 机器人到达目标约 0.15m 处后无限制震荡（42–44s），随后目标被取消。错误信息: `"No valid trajectories out of 420!"` / `"RotateToGoal/Nonrotation command near goal"`。

**根因**: 三个相互影响的参数问题：

| 修复项 | 改前 | 改后 | 效果 |
|--------|------|------|------|
| `RotateToGoal.lookahead_time` | -1.0 | 1.0 | 启用正确的旋转轨迹评估 |
| `min_vel_x` / `min_speed_xy` | 0.05 | 0.0 | 允许目标附近生成纯旋转轨迹 |
| `yaw_goal_tolerance` | 0.25 rad | 0.5 rad | 降低差速平台收敛难度 |
| `required_movement_radius` | 0.5 m | 0.1 m | 避免微调阶段误报"卡住" |
| `movement_time_allowance` | 10.0 s | 15.0 s | 给微调收敛更多时间 |

**结果**: 应用五项修复后，三个目标全部成功收敛，无震荡。

### 问题 4: Gazebo frame_id 前缀问题

**症状**: 雷达数据的 `frame_id` 为 `scout_mini/base_link/front_lidar_sensor`，与 URDF 定义的链接不匹配。

**修复**: 创建 `scan_frame_fixer.py`，去除 `scout_mini/` 前缀并以正确的 frame_id 重新发布扫描数据。

### 问题 5: 里程计未发布 TF

**症状**: Gazebo DiffDrive 插件通过 Gazebo 话题发布里程计，而非 ROS `/odom`。

**修复**: 桥接 Gazebo 的 `/odom_raw`，添加 `imu_odom_corrector.py` 融合 IMU 角速度数据，添加 `odom_to_tf.py` 发布 `odom → base_link` TF。

---

## 12. 局限性

1. **目标收敛时间**: 差速驱动的 DWB 控制器在目标附近可能需要 10–44s 收敛，尤其在对角线路径上。这是非完整约束平台的 xy + yaw 双重容差检查所固有的。

2. **Gazebo frame_id 行为**: Gazebo 会在传感器 frame_id 前加上模型名称前缀，需要 `scan_frame_fixer.py` 作为变通方案。真实机器人不需要此处理。

3. **地图依赖**: 导航需要预建的静态地图。如果 Gazebo 世界发生变化，需要重新运行 SLAM。

4. **真实机器人单雷达**: 仿真使用双雷达融合实现 360° 覆盖。真实机器人配置默认使用单个前雷达。如果有双雷达可用，需要更新 `laser_merger.py`。

5. **Docker 网络**: 容器使用 `--net=host` 实现 DDS 发现。在标准 Linux 主机上工作正常，但在某些防火墙或 VPN 环境下可能有问题。

6. **性能开销**: 同时运行 Gazebo、Nav2 和 RViz2 消耗大量 CPU/GPU。在资源有限的机器上，建议在容器外运行 RViz2。

---

## 13. 物理机器人测试准备

仓库包含分离的配置文件和面向真实机器人部署的完整检查表。

### 配置分离

| 方面 | 仿真 | 真实机器人 |
|------|------|------------|
| 时间源 | `use_sim_time: True` | `use_sim_time: False` |
| 扫描话题 | `/merged/scan` | `/front/scan` |
| 速度限制 | 0.5 m/s, 1.0 rad/s | 0.3 m/s, 0.5 rad/s |
| 启动文件 | `nav2_simulation_launch.py` | `nav2_real_robot_launch.py` |
| 配置文件 | `config/simulation/nav2_params.yaml` | `config/real_robot/nav2_params.yaml` |

### 部署检查表（6 阶段）

| 阶段 | 重点 | 关键项目 |
|------|------|----------|
| 1 | 安全 | 急停验证、电池检查、抬起机器人 |
| 2 | 通信 | CAN 接口（`can0` 500kbps）、雷达 IP 地址 |
| 3 | 验证 | TF 树、里程计、雷达数据质量（不移动） |
| 4 | 电机测试 | 抬起状态的 `cmd_vel` 测试，然后以 0.05 m/s 地面接触测试 |
| 5 | Nav2 测试 | 直线 → 原地转向 → 多点导航（无障碍物） |
| 6 | 关机 | 节点停止、CAN 关闭、电池断开 |

定义了 8 个紧急停止条件。完整检查表: [`reports/real_robot_testing_checklist.md`](reports/real_robot_testing_checklist.md)。

---

## 14. 结论

本项目成功实现了基于 ROS2 Humble 和 Nav2 框架的 Scout Mini 机器人自主导航系统。

### 关键成果

- **完整仿真流水线**: 一键启动即可运行 Gazebo 世界、带双雷达的 Scout Mini 机器人、Nav2 导航栈和 RViz2 可视化。
- **经过验证的导航性能**: 三目标点导航测试达到 100% 成功率（3/3 目标到达）。
- **参数调优**: 优化了五项 DWB 控制器参数，解决了差速驱动平台特有的目标收敛震荡问题。
- **干净构建可复现性**: 全部 6 个包从零构建仅需 1.22s，零错误——无需未记录的手动步骤。
- **真实机器人就绪**: 分离了仿真和真实机器人配置，准备了完整的 6 阶段部署检查表，为首次物理测试设置了保守速度限制。
- **文档完备**: 最终 README 覆盖从 Docker 设置到导航测试的全部步骤，包含故障排除和已知局限性。

### 系统验证汇总

| 指标 | 结果 |
|------|------|
| 成功构建的包 | 6/6 (100%) |
| 干净构建时间 | 1.22s |
| 导航成功率 | 3/3 (100%) |
| 目标 1 耗时 | ~4s |
| 目标 2 耗时 | ~15s |
| 目标 3 耗时 | ~14s（调优后） |
| 雷达频率 | ~10 Hz（双传感器） |
| TF 树完整性 | 已验证正确 |
| 配置分离 | 仿真 + 真实机器人 |
| 文档完整度 | 含 13 节 README + 6 份任务报告 |

### 证据汇总

| 证据 | 路径 |
|------|------|
| Gazebo 截图 | `media/screenshots/task16_gazebo.png` |
| RViz2 截图（3 个目标） | `media/screenshots/task22 goal*.png` |
| TF 树 | `media/screenshots/task18_tf.png` |
| 双雷达可视化 | `media/screenshots/task15.png` |
| 导航视频 | `media/task22 vedio.webm` |
| 三目标终端日志 | `media/LOG/task22.log` |
| 系统架构图 | 本报告及 README 中 |
| 话题列表 | 本报告（第 7 节） |

系统已准备好按 [`reports/real_robot_testing_checklist.md`](reports/real_robot_testing_checklist.md) 中的检查表部署到物理 Scout Mini 机器人上。

---

*报告完*
