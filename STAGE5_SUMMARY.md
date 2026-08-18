# 阶段 5 进展总结：仿真抓取与放置（Pick-and-Place Demo）

## 已完成

| 项目 | 内容 |
|---|---|
| Dockerfile | 添加 5 个 ros2_control apt 包（ros2_control / ros2_controllers / joint_trajectory_controller / joint_state_broadcaster / ign_ros2_control） |
| URDF | joint1~7 加 transmission + `ros2_control`（IgnitionSystem 硬件插件）+ Gazebo 插件；移除 Gazebo joint_state_publisher；joint8 加 mimic；piper_mount.xacro 加 DetachableJoint 插件（parent_link=link7） |
| 配置 | `piper_controllers.yaml`（controller_manager + 3 个 controller）；`manipulation_waypoints.yaml`（全部 waypoints / 夹爪 / 时间 / spawn / attach 参数化） |
| IoT 模型 | `iot_device.sdf`（0.1×0.1×0.05 m、0.2 kg 自由刚体） |
| 核心节点 | `manipulation_node.py` 状态机：取货（home→pick→夹爪闭合→attach→carry）+ 订阅 `/deployment_status` 放置（place→detach→松开→home）+ 初始 detach |
| launch / CMake | spawner 串联激活（`--switch-timeout 90`）+ iot spawn + manipulation_node |
| run.sh | 加 `--shm-size=1g`（**关键**，解决 FastDDS SHM 段创建失败） |
| 调优 | place / place_above 用 FK 调优到夹爪在 base 前方 0.35 m、地面高 0.52 m（对准 0.5 m 台面） |
| **端到端已验证** | controllers 激活 → 初始 detach → 取货（attach `Creating detachable joint`）→ 导航成功 → READY → 放置（detach）→ `DEPLOYMENT_COMPLETE` |

## 剩余未完成

1. **设备落到台面验证** —— FK 调优后尚未重跑确认设备真正停在 0.5 m 台面（之前落在地面）
2. **回归测试** —— 不可达目标仍收 `DEPLOYMENT_FAILED` 且机械臂保持携带位
3. **README.md 更新** —— 抓取流程与新 topic 说明
4. **RViz / Gazebo 画面一致性、无明显穿模** —— 需 X11 目检

## 主要问题（Gazebo 仿真）

### 1. /dev/shm 不足（根因，已部分解决）
- FastDDS 用共享内存传输，64 M 默认被 `fastrtps_*` 段占满 → `Failed to create segment` → controller_manager、DDS 通信大面积卡死
- `gz_ros2_control` 首次初始化 controller_manager 需大块 SHM，不足时直接卡死（连 robot_state_publisher 后无下文）
- 已加 `--shm-size=1g` 并重启容器解决；但 64 M 下多次 `kill -9` 残留段会累积，需清理 `/dev/shm/fastrtps_*`

### 2. gz_ros2_control controller_manager 启动慢且时序敏感
- Gazebo 首次启动慢，controller_manager 要等 sim 运行才初始化
- spawner 激活超时（默认 5 s）→ 加 `--switch-timeout 90` + 串联激活
- 节点需等 action server 就绪才发轨迹，否则 goal 被 abort（status 5）

### 3. 轨迹 goal abort（当前最后一关）
- 节点取货曾报 `home 轨迹执行状态 5`（goal 挂 100 s 超时），但**手动发同一轨迹 SUCCEEDED**
- 根因：节点在 controllers 未完全 active / sim 未跑起来时发出 goal
- 拟改：取货失败后重置状态、由定时器重启取货流程（提升鲁棒性）

### 4. DetachableJoint 语义
- child model 出现时**立即自动 attach**（设备被焊死在 spawn 点）→ 需启动时先 detach
- 已处理：节点启动后先 `ign topic /iot_device/detach` 释放设备

### 5. 预设轨迹与精确放置的差距
- 固定关节角 + 任意导航候选点，放置点无法精确对准任意目标；当前用 FK 调优对准固定台面场景

---

**当前状态**：sim 在运行（容器已重启、shm 1 G、controllers active、手动轨迹成功），但取货节点已 fail。下一步建议：给节点加"失败后自动重试取货"逻辑后重启做完整验收。
