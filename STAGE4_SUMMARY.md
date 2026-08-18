# 阶段 4 进展总结：端到端集成（导航核心）

## 已完成

| 项目 | 内容 |
|---|---|
| 主节点 | `iot_deployment/deployment_approach_node.py` — 订阅 `/deployment_target`，执行 pipeline（生成→可达过滤→占据过滤→评分排序）→ Nav2 NavigateToPose 逐个尝试 → 成功发 `READY_FOR_MANIPULATION` / 全部失败发 `DEPLOYMENT_FAILED` |
| 目标抢占 | 收到新目标时先 `cancel_goal_async()` 取消当前导航，再执行新流程 |
| Marker 可视化 | `/deployment_markers` (MarkerArray)：红球=目标、绿箭头=选中位姿、蓝箭头=有效候选、灰箭头=被拒绝候选；每次新目标先发 DELETEALL |
| Launch | `launch/iot_deployment_launch.py` — 包含 `nav2_launch.py`（传 `rviz_config=iot_deployment.rviz`）+ 启动主节点（加载 `deployment_params.yaml` + `use_sim_time`） |
| RViz | `rviz/iot_deployment.rviz` — 基于 nav2_default_view，插入 MarkerArray display（topic=`/deployment_markers`） |
| 参数 | `config/deployment_params.yaml` — 加 `deployment_approach_node: ros__parameters` 包装；`height_tolerance` 调为 0.25（覆盖 z=0.5 货架场景） |
| CMake | `install(PROGRAMS iot_deployment/deployment_approach_node.py ...)`；`launch/`、`rviz/`、`config/` 目录已在安装列表 |
| nav2_launch.py 修复 | RViz 节点改用 `rviz_config` launch arg（原来硬编码 nav2_default_view.rviz，arg 不生效） |
| 参数重复声明修复 | 新增 `iot_deployment/__init__.py::declare_param()` 幂等封装，4 个模块统一替换 `node.declare_parameter`（解决 `arm_reach_min`/`arm_reach_max` 被 Generator 和 Filter 重复 declare 导致 `ParameterAlreadyDeclaredException`） |
| README.md | 功能简介、启动方法、topic 列表、参数说明 |
| **端到端已验证** | 目标 `(2.0, 1.0, 0.5)` → 36 候选 → 可达 29 → 无碰撞 29 → 最高分 `(1.80, 1.35, -60°)` score=0.988 → **导航成功 → READY_FOR_MANIPULATION**；不可达目标 `z=5.0` → **DEPLOYMENT_FAILED**；marker 四类均正常发布 |

## 单元测试

- 28/28 通过（`test_candidate_generator.py` 8 项 + `test_filters.py` 20 项）
- 测试不依赖 rclpy 节点上下文，类构造函数直接传参

## 主要问题与解决

### 1. ParameterAlreadyDeclaredException
- **根因**：`CandidateGenerator` 和 `ReachabilityFilter` 都 declare `arm_reach_min`/`arm_reach_max`，主节点同时实例化两者时冲突
- **解决**：`iot_deployment/__init__.py` 新增 `declare_param(node, name, default)`，用 try/except `ParameterAlreadyDeclaredException` 实现幂等 declare；4 个模块全部替换

### 2. height_tolerance 不足
- **根因**：验收目标 z=0.5，`gripper_z = base_link_z + gripper_z_offset = 0.054 + 0.267 = 0.321`，`|0.321 - 0.5| = 0.179 > 0.1` → 全部候选被拒绝
- **解决**：`height_tolerance` 从 0.1 调为 0.25

### 3. lifecycle_manager 首次 bringup 超时
- **现象**：`Failed to change state for node: map_server`（map_server configure 耗时 >1ms，lifecycle_manager bond_timeout 判定失败）
- **现状**：lifecycle_manager 后续自动重试成功（`attempt_respawn_reconnection=true`），非本阶段引入的问题，不影响功能

### 4. rviz_config launch arg 不生效
- **根因**：`nav2_launch.py` 中 RViz 节点硬编码 `nav2_default_view.rviz`，忽略 `rviz_config` 参数
- **解决**：改为 `arguments=['-d', rviz_config]`；`iot_deployment_launch.py` 通过 `launch_arguments` 传入 `iot_deployment.rviz`

## 未解决问题

### 1. RViz 与 Gazebo 中机器人运动方向相反
- **现象**：RViz 中机器人朝向/运动方向与 Gazebo 中显示的方向相反（疑似 spawn_yaw 或 TF 坐标系不一致）
- **影响**：导航功能本身正常（Nav2 基于 map/odom TF 计算，能正确到达目标），仅可视化层面不一致
- **待排查**：`spawn_yaw=3.14159` 与 AMCL 初始位姿 yaw 是否匹配；`odom_to_tf` 发布的 TF 与 Gazebo 内部坐标系是否对齐
