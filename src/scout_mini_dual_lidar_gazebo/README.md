# IoT Deployment — Scout Mini + Piper

给定 map 坐标系中的 IoT 目标位姿，自动计算机械臂可达的机器人 base 候选位姿，
经可达性/占据过滤与评分排序后，用 Nav2 导航到最优候选，
抵达后由 Piper 机械臂完成 IoT 设备的抓取与放置。

完整流程分两个阶段：

1. **取货（启动即自动执行）**：机械臂从 home 位移动到取货台上方 → 下降到
   取货位 → 夹爪闭合 → 将 IoT 设备 attach 到夹爪 → 抬起 → 保持携带姿态。
2. **放置（取货完成后自动触发）**：取货完成后 `manipulation_node` 自动发布
   放置目标到 `/deployment_target`，Nav2 导航到候选位姿；导航成功后机械臂
   从携带位 → 放置台上方 → 下降到放置位 → detach 释放设备 → 夹爪松开 →
   抬起 → 回到 home，并发布 `DEPLOYMENT_COMPLETE`。

抓取使用 Gazebo Sim 的 `DetachableJoint` 插件模拟：到达取货位后把 IoT 设备
焊接（attach）到夹爪 link7，放置时断开焊接（detach）让设备留在台面上。
不使用 MoveIt / IK / 真实抓取物理。

## 启动

```bash
# 编译（iot_deployment/ 下 Python 模块修改后必须重新 build）
cd /ws && colcon build --symlink-install
source /ws/install/setup.bash

# 启动 Gazebo + Nav2 + deployment_approach_node + ros2_control + manipulation_node
ros2 launch scout_mini_dual_lidar_gazebo iot_deployment_launch.py
```

启动后流程全自动：机械臂自动取货并保持携带姿态，取货完成后自动发布放置
目标触发导航，导航成功后自动执行放置。默认无需手动注入目标。

如需手动指定放置目标（覆盖自动目标），执行：

```bash
ros2 topic pub --once /deployment_target geometry_msgs/PoseStamped \
  "{header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0, z: 0.5}, orientation: {w: 1.0}}}"
```

收到新目标时会自动取消正在进行的导航，重新执行完整流程。

## 验收

```bash
# 监听放置完成状态
ros2 topic echo /manipulation_status
# 期望收到: DEPLOYMENT_COMPLETE
```

## Topic

| Topic | 类型 | 方向 | 说明 |
|-------|------|------|------|
| `/deployment_target` | `geometry_msgs/PoseStamped` | 订阅/发布 | 目标位姿，`frame_id` 必须为 `map`；manipulation_node 取货完成后自动发布 |
| `/deployment_status` | `std_msgs/String` | 订阅 | `READY_FOR_MANIPULATION`（导航成功）/ `DEPLOYMENT_FAILED`（全部候选失败） |
| `/manipulation_status` | `std_msgs/String` | 发布 | `DEPLOYMENT_COMPLETE`（放置成功）/ `MANIPULATION_FAILED`（抓取或放置失败） |
| `/deployment_markers` | `visualization_msgs/MarkerArray` | 发布 | 红球=目标，绿箭头=选中位姿，蓝箭头=有效候选，灰箭头=被拒绝候选 |
| `/map` | `nav_msgs/OccupancyGrid` | 订阅 | 占据过滤用地图 |
| `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | ActionClient | Nav2 导航 |
| `arm_controller/follow_joint_trajectory` | `control_msgs/FollowJointTrajectory` | ActionClient | 机械臂 6 轴轨迹控制 |
| `gripper_controller/follow_joint_trajectory` | `control_msgs/FollowJointTrajectory` | ActionClient | 夹爪 joint7 开合控制 |

## 参数

### config/deployment_params.yaml（导航编排）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `arm_reach_min` | 0.20 | 机械臂近距离死区 (m) |
| `arm_reach_max` | 0.60 | 机械臂最大工作半径 (m) |
| `candidate_radius_count` | 3 | 候选圈数 |
| `candidate_angle_step` | 30.0 | 每圈角度步长 (度) |
| `base_link_z` | 0.054 | 机械臂安装高度 (m) |
| `gripper_z_offset` | 0.267 | 抓取高度偏移 (m) |
| `height_tolerance` | 0.25 | 目标高度容差 (m) |
| `robot_radius` | 0.25 | 底盘占据检查半径 (m) |
| `map_required` | false | 地图未收到时是否拒绝全部候选 |
| `score_distance_weight` | 0.6 | 评分距离权重 |
| `score_heading_weight` | 0.4 | 评分朝向权重 |
| `ideal_reach_ratio` | 0.7 | 理想距离占臂展比例 |
| `reach_sigma` | 0.1 | 距离高斯评分标准差 (m) |

### config/manipulation_waypoints.yaml（抓取放置）

机械臂所有关节轨迹位姿（home / pick_above / pick / carry / place_above /
place）、夹爪开合值、运动时长、attach/detach 的话题与模型名、IoT 设备
spawn 位置、放置目标坐标均在此文件中参数化，代码中不硬编码任何关节值。

### config/piper_controllers.yaml（ros2_control）

`joint_state_broadcaster`、`arm_controller`（joint1~6 轨迹）、
`gripper_controller`（joint7 开合）的控制器定义，由 launch 中的 spawner
按顺序加载激活。
