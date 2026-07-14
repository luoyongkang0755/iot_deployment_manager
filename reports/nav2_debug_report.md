# Nav2 导航调试报告

## 问题现象

启动 Nav2 导航后，设置导航目标最终失败，日志显示回收行为（backup → wait → clear costmap）轮了一遍后目标失败：

```
[bt_navigator] [navigate_to_pose] [ActionServer] Aborting handle.
[bt_navigator] Goal failed
```

## 根因分析

经过逐步排查，发现三个关键问题：

### 1. DWB 控制器参数导致机器人不运动

**原因**：`min_vel_x: 0.0` 导致零速度轨迹评分最优时机器人不发出速度指令，同时 `trans_stopped_velocity: 0.25` 远大于最小速度，progress checker 判定机器人"已停止"，10 秒后超时报失败。

**修复**（`config/nav2_params.yaml`）：

| 参数 | 改前 | 改后 |
|------|------|------|
| `min_vel_x` | 0.0 | 0.05 |
| `min_speed_xy` | 0.0 | 0.05 |
| `trans_stopped_velocity` | 0.25 | 0.03 |

### 2. 行为树 InitialPoseReceived 条件卡住流程

**原因**：`navigate_w_recovery.xml` 中 `InitialPoseReceived` 条件节点依赖 blackboard 上的 `initial_pose_received` 变量，该变量在较新版本的 Nav2 中不会自动设置，导致行为树流程卡在路径规划之前。

**修复**：创建 `config/navigate_no_init_check.xml`，去掉 `InitialPoseReceived` / `Sequence` 包裹，让 `ComputePathToPose` 直接执行。

### 3. 行为树节点缺少 blackboard 端口绑定

**原因**：`ComputePathToPose` 和 `FollowPath` 节点未声明输入输出端口（`goal`、`path`），导致 blackboard 数据无法在节点间传递。

**修复**（两个行为树文件）：

```xml
<!-- 改前 -->
<ComputePathToPose name="ComputePathToPose"/>
<FollowPath name="FollowPath"/>

<!-- 改后 -->
<ComputePathToPose goal="{goal}" path="{path}" planner_id="GridBased" name="ComputePathToPose"/>
<FollowPath path="{path}" controller_id="FollowPath" name="FollowPath"/>
```

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `config/nav2_params.yaml` | DWB 控制器参数调整 |
| `config/navigate_no_init_check.xml` | **新建**，去掉 InitialPoseReceived 检查 + 添加端口绑定 |
| `config/navigate_w_recovery.xml` | 添加节点端口绑定 |
| `launch/nav2_launch.py` | bt_navigator 行为树路径指向新文件 |

## 验证结果

修复后重启 launch，设置初始位姿和导航目标，机器人成功规划路径并移动到目标点。
