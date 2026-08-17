# 技术路径详解手册（答辩深挖用）

> 本文档逐条讲解本项目每条技术路径：**涉及文件 → 关键内容 → 底层原理 → 老师可能的提问与答法**。
> 与 `PROJECT_LEARNING_DOC.md`（项目总览）互补，本文档目的是让你经得起逐文件深挖。

---

## 目录

| # | 技术路径 | 核心文件数 |
|---|---------|-----------|
| 1 | 仿真环境（Gazebo Fortress + 世界文件） | 3 |
| 2 | 机器人模型（URDF/xacro + Piper 挂载） | 3 |
| 3 | 机械臂控制链（ros2_control） | 3 |
| 4 | 模拟抓取（DetachableJoint） | 2 |
| 5 | 放置校正（set_pose 服务） | 1 |
| 6 | 传感数据链（桥接 + 修正 + 雷达融合） | 4 |
| 7 | 里程计融合（EKF） | 2 |
| 8 | 全局定位（AMCL） | 1 |
| 9 | Nav2 规划与控制 | 1 |
| 10 | 部署决策流水线（候选 → 过滤 → 评分） | 5 |
| 11 | 导航编排（deployment_approach_node） | 1 |
| 12 | 抓放状态机（manipulation_node） | 2 |
| 13 | 端到端启动编排 | 1 |
| 14 | 基准测试 | 2 |

---

## 1. 仿真环境

### 涉及文件

| 文件 | 作用 |
|------|------|
| `src/scout_mini_dual_lidar_gazebo/worlds/simple_test_world.world` | 主世界：16×16 m 围墙 + 障碍箱 + **deployment_shelf 放置桌** |
| `src/scout_mini_dual_lidar_gazebo/worlds/iot_device.sdf` | IoT 设备模型：0.06×0.06×0.03 m，0.1 kg 蓝色小盒 |
| `src/scout_mini_dual_lidar_gazebo/worlds/pickup_table.sdf` | 备用四腿桌设计（未在 launch 引用） |

### 关键内容

**deployment_shelf（世界坐标 3.0, -3.0）**，三个 link 组成的悬空桌：

```
tabletop   pose(0, 0, 0.335)    尺寸 0.40×0.30×0.03 → 顶面 z=0.35
pillar     pose(-0.18, 0, 0.16) 尺寸 0.05×0.05×0.32  → 后缘支柱
base_plate pose(-0.18, 0, 0.01) 尺寸 0.10×0.10×0.02  → 底座
```

**iot_device 惯性张量**（答辩可能考）：

$$I_{xx}=I_{yy}=\frac{m}{12}(b^2+c^2)=\frac{0.1}{12}(0.06^2+0.03^2)=3.75\times10^{-5}$$

### 原理与答法

- **问：为什么桌面悬空、支柱在后缘？**
  答：最初支柱在桌子正中央，机器人导航到候选点时被支柱卡住——轮子持续打滑但 Nav2 无法到达目标点。把支柱移到后缘（x=-0.18）后，机器人可从正面无障碍接近桌面。
- **问：设备为什么在运行时 spawn 而不写死在 world？**
  答：spawn 坐标参数化在 `manipulation_waypoints.yaml`（`iot_spawn_x/y/z/yaw`），由 launch 的 `ros_gz_sim create` 在 t=6s 时生成，方便调参不用改 world 文件。
- **问：设备 spawn 在底盘上（x=0.115, z=0.250）怎么算的？**
  答：底盘世界 z=0.181（spawn 高度），机械臂根部 x=0、前雷达 x=0.23，取中间 0.115；设备半高 0.015，所以 z = 0.181 + 0.054(底盘顶) + 0.015 = 0.250。

---

## 2. 机器人模型

### 涉及文件

| 文件 | 作用 |
|------|------|
| `src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro` | 顶层模型：底盘 + 轮子 + 双雷达 + `piper_mount.xacro` |
| `src/scout_mini_dual_lidar_gazebo/urdf/piper_mount.xacro` | Piper 臂挂载 + **DetachableJoint 插件声明** |
| `src/piper_description/urdf/piper_description.xacro` | Piper 6-DOF 臂本体：关节限位、惯量、`<ros2_control>` 声明 |

### 关键内容

**挂载关节**（`piper_mount.xacro` 第 20-25 行）：

```xml
<joint name="piper_mount_joint" type="fixed">
    <origin xyz="0 0 ${chassis_top_z}" rpy="0 0 0"/>
    <parent link="base_link"/>
    <child link="piper_base_link"/>
</joint>
```

`chassis_top_z = 0.054 m`——底盘 `base_link` 到车体顶面的真实高度。

**关节限位**（`piper_description.xacro`，写进 waypoint 时必须遵守）：

| 关节 | 类型 | 限位 (rad) |
|------|------|-----------|
| joint1 基座旋转 | revolute | ±2.618 |
| joint2 肩部俯仰 | revolute | 0 ~ 3.14 |
| joint3 肘部俯仰 | revolute | -2.967 ~ 0 |
| joint4 腕 1 俯仰 | revolute | ±1.745 |
| joint5 腕 2 翻转 | revolute | ±1.22 |
| joint6 法兰旋转 | revolute | ±2.0944 |
| joint7 夹爪平移 | prismatic | 0 ~ 0.035 m（joint8 为 mimic） |

**关节动力学**（每个关节都有）：

```xml
<dynamics damping="1.0" friction="1.0"/>
```

### 原理与答法

- **问：damping/friction 调过吗？为什么是 1.0？**
  答：调过，这是本项目最深的坑。原值 10.0/10.0 时 joint2/joint3 完全不动——控制器显示 `reference=1.5` 但 `feedback≈0`，说明物理引擎里阻尼力矩超过了位置控制的输出力矩。降到 1.0 后恢复正常。
- **问：为什么挂载是 fixed 而不给云台？**
  答：机械臂直接刚性固定在底盘顶面中心，与真实装配一致；底盘朝向由导航的候选点 yaw 保证（先摆好车，再动臂）。
- **问：URDF 和 SDF 的关系？**
  答：Gazebo Fortress 只认 SDF。`robot_state_publisher` 发 URDF 给 RViz/TF；`ros_gz_sim create -topic robot_description` 把 URDF 自动转 SDF 给 Gazebo。转换中 fixed link 会被"lumped"（合并）——这正是 DetachableJoint 必须用 link7 而不是 gripper_base 的原因（见第 4 节）。

---

## 3. 机械臂控制链（ros2_control）

### 涉及文件

| 文件 | 作用 |
|------|------|
| `src/piper_description/urdf/piper_description.xacro`（592-648 行） | `<ros2_control>` 硬件接口声明 + `ign_ros2_control` 插件 |
| `src/scout_mini_dual_lidar_gazebo/config/piper_controllers.yaml` | 三个 controller 的定义 |
| `src/scout_mini_dual_lidar_gazebo/launch/iot_deployment_launch.py`（66-115 行） | controller spawner 的时序编排 |

### 关键内容

**三层架构**：

```
URDF <ros2_control> 声明硬件接口（position 命令 + position/velocity 状态）
    ↓
ign_ros2_control 插件在 Gazebo 进程内创建 /controller_manager
    ↓
三个 controller（piper_controllers.yaml 定义）：
  joint_state_broadcaster  → 发布 /scout_mini/joint_states
  arm_controller           → FollowJointTrajectory action，joint1-6
  gripper_controller       → FollowJointTrajectory action，joint7
```

**controller 定义要点**（`piper_controllers.yaml`）：

- `update_rate: 100` Hz（与 ign_ros2_control 控制环一致）
- 两个轨迹 controller 都是 `joint_trajectory_controller/JointTrajectoryController` 类型，`command_interfaces: [position]`
- 夹爪 joint8 是 joint7 的 mimic，不需要单独 controller

**时序编排**（launch，防竞态的核心）：

```python
delayed_jsb      = TimerAction(period=10.0, actions=[jsb_spawner])
delayed_arm      = TimerAction(period=20.0, actions=[arm_spawner])
delayed_gripper  = TimerAction(period=30.0, actions=[gripper_spawner])
delayed_manipulation = TimerAction(period=45.0, actions=[manipulation_node])
```

三个 spawner 各带 `--switch-timeout 90`，彼此错开 10 秒，`joint_state_broadcaster` 最先。

### 原理与答法

- **问：为什么不把 spawner 放事件处理器（controller_manager 出现就加载）？**
  答：试过。Gazebo 首次启动慢，事件触发后并发 `switch_controller` 会冲突，spawner 激活阶段时序脆弱。改为 TimerAction 错开 + 超时 90s 后，稳定。
- **问：manipulation_node 为什么 45 秒后才起？**
  答：10+10+10+15 的保守预算。节点内部还有兜底：`_startup_once` 每 0.5s 轮询两个 action server，就绪前不动。
- **问：joint_states 为什么经过桥接？**
  答：见第 6 节最后一条——`/scout_mini/joint_states`（ROS 域，由 broadcaster 发布）经 `ros_gz_bridge` 中继到 `/joint_states` 给 `robot_state_publisher`。历史上 Gazebo 自带的 joint-state-publisher 系统插件会和 broadcaster 双源冲突，已从 `scout_mini.gazebo` 移除，保证**单一关节状态源**。
- **问：FollowJointTrajectory 和直接发 position 命令的区别？**
  答：action 接口带执行状态反馈（SUCCEEDED/ABORTED），状态机依赖它判断每步是否完成；直接 topic 命令无回执，无法做失败处理。

---

## 4. 模拟抓取（DetachableJoint）

### 涉及文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `urdf/piper_mount.xacro`（29-44 行） | 插件声明 | 在 scout_mini 模型上加载 DetachableJoint 系统 |
| `iot_deployment/manipulation_node.py`（`_attach`/`_detach`） | 调用端 | 通过 `ign topic` CLI 发 Empty 消息触发焊接/断开 |

### 关键内容

**插件声明**（为什么放在 piper_mount 而不是设备 SDF：插件挂在 parent 模型上，跨模型焊接 child）：

```xml
<plugin filename="ignition-gazebo-detachable-joint-system"
        name="gz::sim::systems::DetachableJoint">
    <parent_link>link7</parent_link>
    <child_model>iot_device</child_model>
    <child_link>iot_device_link</child_link>
    <attach_topic>/iot_device/attach</attach_topic>
    <detach_topic>/iot_device/detach</detach_topic>
</plugin>
```

**触发命令**（`_run_ign_topic`）：

```bash
ign topic -t /iot_device/attach -m ignition.msgs.Empty -p 'unused: true'
```

**两个关键细节**：

1. **初始自动焊接问题**：插件在 child model 出现时会立即自动 attach（语义是"初始已连接"），把设备焊死在 spawn 点。所以取货流程第一步是先 `_detach` 解除初始焊接（`manipulation_node.py` 134-141 行）。
2. **为什么用 link7 不用 gripper_base**：gripper_base 与 link6 是 fixed 连接，URDF→SDF 转换时被 lumped（合并进 link6），SDF 里不是真实 link；link7（夹爪指尖）是真实存在的 link，位于夹爪末端。

### 原理与答法

- **问：为什么不用真实的夹爪夹持物理？**
  答：Gazebo 接触物理对"两指夹小盒"这种场景极不稳定（摩擦锥求解抖动、接触时断时续），成功率为概率性。DetachableJoint 是 Gazebo 官方提供的确定性行为：attach 即创建固定焊接约束，设备严格跟随夹爪；detach 即删除约束，设备留在当前位置。仿真验证算法逻辑用确定性方案，真实抓取物理留给实机。
- **问：为什么用 `ign topic` CLI 而不是 ROS 桥接？**
  答：DetachableJoint 用 gz-transport 的 Empty 消息，`ros_gz_bridge` 对 Empty 类型不桥接（无对应 ROS 消息映射）。用 CLI 起子进程发布是最可靠的方式；子进程有 10s 超时看门狗防挂起。
- **问：attach 之后设备运动学上算什么？**
  答：物理引擎层面创建了一个 fixed constraint（焊接约束），把 `iot_device_link` 的 6 自由度全部约束到 `link7` 上，质量并入动力学求解，所以臂动设备跟着动，且不穿模。

---

## 5. 放置校正（set_pose 服务）

### 涉及文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `iot_deployment/manipulation_node.py`（`_set_device_pose`，428-452 行） | 调用端 | detach 后把设备瞬移到精确目标位姿 |

### 关键内容

```python
pose_proto = (
    f'name: "{self._child_model}" '
    f'position {{ x: {self._target_x} y: {self._target_y} z: {final_z} }} '
    f'orientation {{ x: 0 y: 0 z: 0 w: 1 }}'
)
cmd = ['ign', 'service', '-s', f'/world/{self._world}/set_pose',
       '--reqtype', 'ignition.msgs.Pose', '--reptype', 'ignition.msgs.Boolean',
       '--timeout', '5000', '--req', pose_proto]
```

`final_z = target_z(0.35) + place_z_offset(0.03) = 0.38`——0.03 是设备半高，落在桌面正上方后由重力沉降贴面。

放置序列中它的位置：`place_above → place → detach → settle → set_pose → open → place_above2 → home`

### 原理与答法

- **问：为什么要 set_pose？机械臂直接放不行吗？**
  答：三个误差源叠加——① Nav2 的 `xy_goal_tolerance=0.25m`，机器人实际停点与候选点有几十厘米偏差；② URDF→SDF 转换使 FK 与物理引擎的实际末端位置有约 19 cm 系统偏差；③ 放置 waypoint 只是粗调释放点。set_pose 把最终落点硬性对准 `(target_x, target_y, target_z+offset)`，速度清零，保证验收时设备精确在台面上。
- **问：这算不算作弊？**
  答：这是仿真验证常用手段（类似 moveit 的允许误差注入）。项目定位是验证**决策与编排逻辑**（候选选择、导航、状态机），不是验证接触物理。若做实机，此步天然消失——机械臂真实放置，误差由视觉伺服补偿。
- **问：proto 里 name 字段干什么用？**
  答：`ignition.msgs.Pose` 的 `name` 指定要移动的**模型名**（iot_device）；没有 name 服务不知道改谁。这是调试时踩过的坑：漏了 name 字段服务静默无效。

---

## 6. 传感数据链

### 涉及文件

| 文件 | 作用 |
|------|------|
| `launch/nav2_launch.py`（141-162 行） | `ros_gz_bridge` 桥接表 |
| `src/scan_frame_fixer.py` | 雷达 frame_id 修正：`/front/scan → /front/scan_fixed` |
| `src/laser_merger.py` | 双雷达融合：`/front/scan_fixed + /rear/scan_fixed → /merged/scan` |
| `src/imu_odom_corrector.py` | 里程计 frame_id 修正：`/odom_raw → /odom` |

### 关键内容

**桥接表**（`[` = gz→ROS，`]` = ROS→gz）：

```
/clock [gz→ros]     /cmd_vel [ros→gz]      /odom_raw [gz→ros]
/imu [gz→ros]       /front/scan [gz→ros]   /rear/scan [gz→ros]
/scout_mini/joint_states [ros→gz 中继到 /joint_states]
```

**scan_frame_fixer**：Gazebo 发的雷达 frame_id 带模型前缀（`scout_mini/front_lidar`），TF 树里是 `front_lidar_link`，不一致会导致 TF 查找失败。修正器把它改成 URDF link 名。

**laser_merger 核心逻辑**：
- 每帧只做**一次 TF 查找**并缓存 `(dx, dy, cos yaw, sin yaw)`，把两雷达点云变换到 `base_link` 系
- 输出 `angle_min=-π, angle_max=π` 的 360° LaserScan，frame_id=`base_link`
- 前后雷达各 170° 视场，中间盲区由对方覆盖，合并后全覆盖
- 带椭圆机身滤波（前向加权，遮蔽 Piper 臂对前雷达的自遮挡）

**imu_odom_corrector**：剥掉 frame_id 前缀、统一为 `odom`/`base_link`，位姿速度原样透传（融合交给 EKF）。

### 原理与答法

- **问：为什么不直接用一个 360° 雷达？**
  答：真实 Scout Mini 平台就是前后双 2D 雷达的构型（底盘前后各有安装位），仿真对齐实机硬件。双雷达融合是感知层的第一课。
- **问：merged/scan 的优点？**
  答：① 360° 全向感知，无后向盲区；② 输出统一到 `base_link` 系，下游（AMCL/costmap）不用关心两个雷达的安装外参；③ 一次订阅一份消息，降低下游处理开销。
- **问：TF 缓存为什么必要？**
  答：雷达 10+ Hz，每帧每雷达查 TF 有超时异常风险；缓存上次有效变换，瞬时 TF 抖动时仍能继续融合。

---

## 7. 里程计融合（EKF）

### 涉及文件

| 文件 | 作用 |
|------|------|
| `config/ekf_params.yaml` | robot_localization EKF 全部配置 |
| `launch/nav2_launch.py`（196-205 行） | 节点启动 + `odometry/filtered` 重映射到 `/odom` |

### 关键内容

**数据流**：

```
/odom_raw (Gazebo DiffDrive 插件，轮式)
    → imu_odom_corrector (frame_id 清洗) → /odom
/imu (Gazebo IMU)
    ↓
EKF (ekf_node, 30 Hz, two_d_mode) → /odom (重映射) → 发布 odom→base_link TF
```

**融合配置**（15 维布尔向量，核心思想：**谁的量可信就融合谁**）：

- `odom0_config`：x, y 位置 ✓，vx, vyaw ✓，**yaw ✗**（轮式 yaw 打滑不可信）
- `imu0_config`：**yaw ✓（绝对姿态），vyaw ✓（陀螺仪角速度）**，其余全 ✗

**过程噪声**（15×15 对角阵）：位置 0.05，yaw 0.06，速度 0.025——控制 EKF 对自预测的信任度。

### 原理与答法

- **问：为什么要 EKF？轮式里程计不够吗？**
  答：Scout Mini 是滑移转向（skid-steer），转弯时四轮必然侧滑，轮式解算的 yaw 角误差累积很快（实测转弯 90° 可漂 5-10°）。IMU 陀螺仪短时角速度精确、绝对 yaw 无漂移。EKF 用 IMU 的 yaw/vyaw 修正轮式的位置/线速度，输出光滑无漂移的 `odom→base_link`。
- **问：为什么 EKF 只做局部（world_frame=odom）不做全局？**
  答：分层定位架构——EKF 管 odom 系（连续平滑、短时精确），AMCL 管 map→odom（全局校正、离散跳变）。两层分离是 ROS 导航的标准实践，EKF 输出不平滑会污染局部规划。
- **问：协方差在哪调的？**
  答：`ekf_params.yaml` 的 `process_noise_covariance`。原则：值小=信自预测，值大=依赖传感器修正。当前位置 0.05/yaw 0.06 是权衡平滑性与响应速度的经验值。
- **问：EKF 替代了什么？**
  答：替代了原先的 `odom_to_tf` 节点（直接把轮式 odom 转 TF），数据流注释在 yaml 头部有记录。

---

## 8. 全局定位（AMCL）

### 涉及文件

| 文件 | 位置 | 关键参数 |
|------|------|---------|
| `config/nav2_params.yaml` | 5-47 行 | amcl 全部配置 |

### 关键内容

```yaml
set_initial_pose: True          # spawn(0,0,0) 自动初始化
initial_pose: {x: 0.0, y: 0.0, yaw: 0.0}
min_particles: 500 / max_particles: 2000
laser_model_type: likelihood_field    # 似然场观测模型
robot_model_type: DifferentialMotionModel
scan_topic: /merged/scan
laser_max_range: 25.0 / max_beams: 60
update_min_d: 0.25 / update_min_a: 0.2   # 位移/转角超过阈值才重采样
```

**行为树定制**（`launch/nav2_launch.py` 289-292 行）：`default_nav_to_pose_bt_xml` 指向 `config/navigate_no_init_check.xml`——跳过初始位姿检查节点，配合 `set_initial_pose` 实现零人工干预启动。

### 原理与答法

- **问：AMCL 原理一句话？**
  答：自适应蒙特卡洛定位——粒子滤波，用一群带权重的位姿假设（粒子）近似位姿后验分布；运动更新扩散粒子，激光观测（似然场模型）重加权重采样，粒子收敛处即机器人位姿。
- **问：为什么 KLD 采样（500-2000 自适应）？**
  答：不确定度高（如刚启动/绑架）时多粒子保覆盖，收敛后少粒子省算力。nav2_amcl 默认 KLD 采样开启。
- **问：AMCL 发布什么 TF？**
  答：`map → odom`。它不直接给机器人位姿，而是给两个定位层的修正偏移。完整链：`map →(AMCL)→ odom →(EKF)→ base_link`。
- **问：manipulation_node 怎么知道 AMCL 就绪？**
  答：订阅 `/amcl_pose`，收到第一条即置 `_amcl_received=True`；自动发布放置目标前轮询此标志（备用 TF `can_transform('map','base_link')`），避免 map frame 缺失时 Nav2 瞬间拒绝所有候选。
- **问：likelihood_field 和 beam 模型区别？**
  答：beam 模型逐条光线做 ray-casting 匹配（精确但慢）；likelihood_field 预计算占据栅格的距离场，查每个激光端点到最近障碍的距离（快且平滑）。本项目场地开阔，likelihood_field 足够。

---

## 9. Nav2 规划与控制

### 涉及文件

| 文件 | 位置 | 内容 |
|------|------|------|
| `config/nav2_params.yaml` | 49-297 行 | bt_navigator / controller / costmaps / planner / recoveries / waypoint_follower |

### 关键内容

**局部规划器 DWB**（动态窗口法）：

- 速度采样：`vx_samples=20, vtheta_samples=20, sim_time=1.7s`
- 约束：`max_vel_x=0.5, max_vel_theta=1.0, acc_lim_x=1.0`
- 七个 critics 加权评分：`BaseObstacle(0.02) PathAlign(32) GoalAlign(24) PathDist(32) GoalDist(24) RotateToGoal(5) Oscillation`

**全局规划器 NavfnPlanner**：`use_astar=false`（Dijkstra，保证最短路径），`tolerance=0.5`，`allow_unknown=true`。

**双 costmap**：

| | local_costmap | global_costmap |
|---|---|---|
| frame | odom（滚动 3×3 m） | map（全图） |
| 更新频率 | 5 Hz | 1 Hz |
| 插件 | obstacle + inflation | static + obstacle + inflation |
| 输入 | `/merged/scan` | `/merged/scan` + 地图文件 |

共同的 `robot_radius=0.3, inflation_radius=0.55, cost_scaling_factor=3.0`。

**恢复行为**：`spin / backup / wait`，行为树卡住时按序触发。

**控制器频率与容差**：`controller_frequency=20 Hz, xy_goal_tolerance=0.25 m, yaw_goal_tolerance=0.5 rad, failure_tolerance=0.3 s`。

### 原理与答法

- **问：DWB 原理？**
  答：动态窗口法——在加速度约束构成的可行速度集合（动态窗口）内采样 (v, ω) 组合，前向模拟 `sim_time` 时间得到预测轨迹，用多个 critics 加权打分，选最优速度下发。20 Hz 循环滚动。
- **问：为什么 inflation_radius=0.55 比 robot_radius=0.3 大这么多？**
  答：膨胀层在障碍周围生成代价梯度（指数衰减，`cost_scaling_factor=3.0`），0.55 的膨胀半径让路径在离障碍 25cm 处就开始平滑避让，而不是贴边走。代价梯度是"软约束"，给局部规划器提供连续的推离力。
- **问：xy_goal_tolerance=0.25 够准吗？**
  答：单看不够，这正是本项目候选点 + proximity_threshold 设计的原因：导航容差内到达后，接近即停逻辑判断实际距离 ≤1.0 m 也算到达，最终放置精度由 set_pose 兜底（见第 5 节）。误差链：Nav2 容差(0.25) → 接近判定(1.0) → set_pose 归零。
- **问：NavfnPlanner 和 SmacPlanner 选型？**
  答：Navfn 是 Dijkstra 波前扩展，网格地图上快且够用；Smac 支持 hybrid-A*（考虑运动学）适合阿克曼结构。Scout Mini 是差速可原地转，无需运动学感知规划器。
- **问：为什么 controller_frequency=20？**
  答：与雷达 10 Hz 匹配的 2 倍过采样，局部规划有足够刷新率又不空转。DWB 每周期前向模拟 20×20=400 条轨迹，20 Hz 下 CPU 占用可控。

---

## 10. 部署决策流水线

### 涉及文件

| 文件 | 类 | 职责 |
|------|-----|------|
| `iot_deployment/candidate_generator.py` | `CandidateGenerator` | 环形采样生成候选 |
| `iot_deployment/reachability_filter.py` | `ReachabilityFilter` | 几何可达性过滤 |
| `iot_deployment/occupancy_filter.py` | `OccupancyFilter` | 占据栅格碰撞过滤 |
| `iot_deployment/candidate_scorer.py` | `CandidateScorer` | 高斯+朝向加权评分 |
| `config/deployment_params.yaml` | — | 全部参数 |

每个模块都支持**双构造**（`node=` 从 ROS 参数读 / 直接传参），`test/` 下有对应单元测试（`test_candidate_generator.py`、`test_filters.py`）。

### 关键内容

**候选生成**（数学）：

$$x_k = t_x + r\cos\theta_k,\quad y_k = t_y + r\sin\theta_k,\quad \theta_k = k \cdot 30°,\quad r \in \{0.25, 0.50\}$$

`yaw = atan2(t_y - y, t_x - x)`——**朝向目标**。2 圈 × 12 角 = 24 个候选。

**可达性过滤**两检查：

1. 高度：`gripper_z = base_link_z(0.054) + gripper_z_offset(0.267) = 0.321`，与 `target_z` 差 ≤ `height_tolerance(0.25)` 才放行（0.35 桌面在容差内）。全否决时直接判目标不可达。
2. 距离：候选到目标 2D 距离 ∈ [0.25, 0.50]。

**占据过滤**：候选为圆心、`robot_radius=0.25` 为半径的圆内所有栅格，存在占据（>50）或未知（<0）即拒绝。地图未收到时 `map_required=false` 跳过检查（只 warn）。

**评分**：

$$S = 0.6 \cdot e^{-\frac{(d - 0.7 \cdot 0.5)^2}{2 \cdot 0.1^2}} + 0.4 \cdot \frac{1+\cos(\Delta\theta)}{2}$$

理想距离 0.35 m（`arm_reach_max × ideal_reach_ratio`），高斯 σ=0.1。

### 原理与答法

- **问：为什么环形采样而不是栅格全域搜索？**
  答：目标已定，机械臂工作半径已知（[0.25, 0.50]），基座只可能落在环带上。24 个候选的计算量远小于 16×16 m 地图全域栅格枚举，且每个都保证机械臂"够得着"。
- **问：距离分为什么是高斯不是线性惩罚？**
  答：高斯在理想距离处平坦、偏离时快速衰减，对"接近理想"的候选宽容（0.30-0.40 都高分），远离时果断放弃。线性惩罚会过度歧视稍偏的候选。
- **问：朝向分 0.4 权重的意义？**
  答：候选 yaw 朝目标保证机械臂正对放置点工作（Piper 是 6-DOF 但工作空间最舒适在前方）。`cos` 形式对 ±90° 内的偏差平滑容忍。
- **问：过滤顺序能换吗？**
  答：先可达（纯几何，O(1)/候选）再占据（栅格查询，O(r²/res²)/候选）——便宜的先跑，贵的只处理幸存者。经典 funnel 优化。
- **问：参数怎么定的？**
  答：`arm_reach_min` 从 0.20 调到 0.25——桌沿到支柱的几何实测；`height_tolerance` 0.25 覆盖 z=0.5 货架场景；评分权重 0.6/0.4 经 RViz marker 可视化多轮调优。

---

## 11. 导航编排（deployment_approach_node）

### 涉及文件

| 文件 | 行数 | 作用 |
|------|------|------|
| `iot_deployment/deployment_approach_node.py` | ~330 行 | 主编排节点 |

### 关键内容

**流水线**（`_run_pipeline`）：

```
/deployment_target (map 系 PoseStamped)
  → generate (24) → reachability.filter → occupancy.filter → scorer.score
  → sorted 降序 → _try_next_candidate 循环：
      NavigateToPose action 发送候选位姿
      ├─ SUCCEEDED → 发布 READY_FOR_MANIPULATION（停止）
      ├─ CANCELED → 新目标到来，弃旧流程
      ├─ ABORTED + 距目标 ≤ proximity_threshold(1.0m) → 视为到达 → READY
      └─ ABORTED 其他 → nav_index+1 尝试下一候选
  → 全部失败 → DEPLOYMENT_FAILED
```

**接近即停**（`_result_callback` + `_is_close_to_target`）：订阅 `/amcl_pose` 跟踪机器人位置；导航 ABORTED（如撞到桌子边缘被迫停）但距离 ≤1.0 m 时判定"实际已到位"。

**Marker 可视化**（`_publish_markers`）：红球=目标，蓝箭头=有效候选，灰箭头=被拒候选，绿箭头（放大）=选中位姿。每次发 MarkerArray 前先 DELETEALL 清旧。

**四元数转换**：yaw → `(0, 0, sin(yaw/2), cos(yaw/2))`。

### 原理与答法

- **问：为什么逐个尝试而不是一次发最优？**
  答：评分是静态先验（距离+朝向），真实可达性受动态障碍影响。逐个尝试是**带回退的贪心**：最优不行换次优，最多 24 次，鲁棒性远高于单发。
- **问：proximity_threshold 的意义？**
  答：机器人逼近桌沿时物理接触导致 Nav2 判 ABORTED，但此时距目标可能只有 0.6 m——机械臂够得着。阈值 1.0 m 是 `arm_reach_max(0.5) + 导航容差(0.25) + 余量` 的工程估计。没有它，机器人会在桌前反复尝试并失败。
- **问：新目标来了怎么处理旧导航？**
  答：`_target_callback` 里对旧 goal_handle 调 `cancel_goal_async()`，收到 CANCELED 状态时不再推进旧流程索引。
- **问：frame 为什么必须是 map？**
  答：候选生成在 map 系做几何运算，Nav2 目标也要求 map 系；其他 frame 直接拒绝并报错（防御式校验）。

---

## 12. 抓放状态机（manipulation_node）

### 涉及文件

| 文件 | 作用 |
|------|------|
| `iot_deployment/manipulation_node.py`（~530 行） | 状态机主体 |
| `config/manipulation_waypoints.yaml` | 全部位姿/时序/模型名参数 |

### 关键内容

**设计原则：yaml 驱动，代码零硬编码**。所有关节值、时长、模型名、spawn 点、目标点都在 yaml。

**取货序列**（9 步）：

```
home → open → pick_above → pick → close → attach → settle(0.5s)
     → pick_above2 → carry
```

**放置序列**（8 步）：

```
place_above → place → detach → settle(0.5s) → set_pose
            → open → place_above2 → home
```

**异步步骤链**（`_run_steps`）：每步是 `fn(done_cb)`，成功回调进下一步，失败走 `on_fail`。异常也兜底（`try/except` 保证状态机不卡死）。

**四个状态标志**：`_holding`（设备在手上）、`_picked`（取货完成）、`_busy`（序列执行中）、`_ready_pending`（READY 先于取货完成到达）。

**关键容错**：

1. 取货失败自动重试（最多 5 次，间隔 3s）——启动时序竞态导致轨迹 abort 的场景
2. 轨迹执行看门狗：`duration + 10s` 超时判失败，防 result 回调丢失永久挂起
3. 放置后回位（home）失败仍发 COMPLETE——设备已 detach，主体成功
4. `_ready_pending`：READY 比 pick 完成先到时暂存，pick 完成后立即执行放置

**自动触发链**（无人干预的关键）：

```
取货完成 → 轮询 AMCL 就绪(≤120s) → 自动发布 /deployment_target
       → approach 节点导航 → READY → place → COMPLETE
```

### 原理与答法

- **问：为什么用回调链不用多线程？**
  答：ROS 2 单线程 executor 下回调链是天然的可串行异步模型——每步完成才进下一步，无锁、无竞态、日志有序。多线程反而要管同步原语。
- **问：单点 waypoint 为什么不用多段轨迹插值？**
  答：`JointTrajectoryController` 收单点目标后内部做线性插值平滑过渡（3s 时长），够用。多 waypoint 插值适合需要控制路径形状的场景（如避障弧线）。
- **问：mock_pick 干什么的？**
  答：跳过取货直接进放置流程，调试放置环节时不用等取货 20s。教训：CLI `manipulation_node.mock_pick:=true` 曾因参数未在 yaml 声明而不生效，修复是在 yaml 显式声明 `mock_pick: false` 后 CLI 覆盖才起作用（ROS 2 参数覆盖机制要求节点先 declare）。
- **问：settle 0.5s 的意义？**
  答：attach/detach 是物理引擎创建/删除约束，需要几个仿真步收敛；立刻动臂会出现设备 lag 或抖动。0.5s 足够约束稳定。

---

## 13. 端到端启动编排

### 涉及文件

| 文件 | 作用 |
|------|------|
| `launch/iot_deployment_launch.py` | 顶层 launch：include nav2 + 部署节点 + spawner + manipulation |

### 关键内容

**启动时序总表**：

| t (s) | 组件 | 说明 |
|-------|------|------|
| 0 | nav2_launch include | Gazebo + 机器人 + 传感链 + Nav2 全家 + RViz(iot_deployment.rviz) |
| 0 | deployment_approach_node | 加载 deployment_params.yaml |
| 6 | iot_device spawn | 坐标从 manipulation_waypoints.yaml 读 |
| 10 | jsb spawner | joint_state_broadcaster |
| 20 | arm spawner | arm_controller |
| 30 | gripper spawner | gripper_controller |
| 45 | manipulation_node | 内部再等 action server 就绪 |

**RViz 配置**：`rviz/iot_deployment.rviz` 含 MarkerArray display、TF、costmap、路径显示。

### 原理与答法

- **问：为什么 6 秒就 spawn 设备，45 秒才起 manipulation？**
  答：设备是静态刚体，Gazebo 起来后即可生成；manipulation 依赖三个 controller 全部 active（最晚 30s+激活耗时），45s 是含余量的保守值。节点内部还有轮询兜底，实际首次就绪即动。
- **问：整个 launch 的进程数？**
  答：约 20+：Gazebo(1) + robot_state_publisher + bridge + 3 个修正/融合节点 + EKF + Nav2 7 节点 + lifecycle_manager + RViz + approach + 3 spawner + manipulation + 设备 spawn。全在一个 docker 容器（scout_nav2）内跑。
- **问：controller spawner 的 --switch-timeout 90？**
  答：Gazebo 首启时 ign_ros2_control 初始化慢，默认 30s 超时不够，spawner 会误报激活失败。90s 消除竞态误报。

---

## 14. 基准测试

### 涉及文件

| 文件 | 作用 |
|------|------|
| `scripts/benchmark_run.py` | 宿主机连跑脚本：docker restart → launch → 日志解析 → CSV |
| `benchmark_results.csv` | 10 轮实测数据 |

### 关键内容

- 6 个日志关键字锚定阶段时间戳（取货开始/完成、导航开始/成功、放置开始/完成），wall time 计时
- 每轮 `docker restart` 保证环境完全干净
- 单轮 360s 超时防挂起
- 结果：**8/10 成功（80%）**，取货 20.0s±0.12s，导航 14.8s 均值，放置 21.1s 均值

### 原理与答法

- **问：为什么用 wall time 不用 sim time？**
  答：论文要报真实耗时。sim time 与 wall time 的比率受 CPU 负载影响（实时因子 <1 时 sim 走得慢），wall time 才反映用户感知的执行时长。
- **问：2 次失败怎么解释？**
  答：第 5、7 轮 timeout 且无任何阶段日志（连取货开始都没有），是 docker restart 后 Gazebo/controller 启动竞态，不是算法失败。进入运行态的 8 轮全部成功。改进方向：脚本加 controller 就绪探测（轮询 `/controller_manager` 服务）再开始计时。

---

## 附：高频追问速查

| 追问 | 一句话答 |
|------|---------|
| 为什么不用 MoveIt？ | URDF→SDF 偏差 19cm 使 FK 不可信，IK 规划无意义；固定场景用预设 waypoint + set_pose 兜底更确定 |
| 抓取是假的吗？ | 仿真用 DetachableJoint 确定性焊接，验证决策链；真实夹持物理是实机阶段课题 |
| 误差链怎么闭环的？ | Nav2 容差 0.25 → 接近判定 1.0 → set_pose 归零 |
| TF 树几层？ | map→(AMCL)→odom→(EKF)→base_link→(fixed/revolute)→雷达/臂 |
| 参数都能在哪改？ | 全部 yaml 化，代码零硬编码（deployment_params / manipulation_waypoints / nav2_params / ekf_params / piper_controllers） |
| 单元测试有吗？ | test_candidate_generator.py + test_filters.py 覆盖纯逻辑模块 |
| 怎么复现实验？ | `python3 scripts/benchmark_run.py 10` 一键 10 轮出 CSV |
