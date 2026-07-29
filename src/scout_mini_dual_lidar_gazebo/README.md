# IoT Deployment — Scout Mini + Piper

给定 map 坐标系中的 IoT 目标位姿，自动计算机械臂可达的机器人 base 候选位姿，
经可达性/占据过滤与评分排序后，用 Nav2 导航到最优候选，
抵达后发布 `READY_FOR_MANIPULATION`，供后续抓取流程使用。

## 启动

```bash
# 编译（iot_deployment/ 下 Python 模块修改后必须重新 build）
cd /ws && colcon build --symlink-install
source /ws/install/setup.bash

# 启动 Gazebo + Nav2 + deployment_approach_node
ros2 launch scout_mini_dual_lidar_gazebo iot_deployment_launch.py
```

## 触发部署

```bash
ros2 topic pub --once /deployment_target geometry_msgs/PoseStamped \
  "{header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0, z: 0.5}, orientation: {w: 1.0}}}"
```

收到新目标时会自动取消正在进行的导航，重新执行完整流程。

## Topic

| Topic | 类型 | 方向 | 说明 |
|-------|------|------|------|
| `/deployment_target` | `geometry_msgs/PoseStamped` | 订阅 | 目标位姿，`frame_id` 必须为 `map` |
| `/deployment_status` | `std_msgs/String` | 发布 | `READY_FOR_MANIPULATION` / `DEPLOYMENT_FAILED` |
| `/deployment_markers` | `visualization_msgs/MarkerArray` | 发布 | 红球=目标，绿箭头=选中位姿，蓝箭头=有效候选，灰箭头=被拒绝候选 |
| `/map` | `nav_msgs/OccupancyGrid` | 订阅 | 占据过滤用地图 |
| `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | ActionClient | Nav2 导航 |

## 参数（config/deployment_params.yaml）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `arm_reach_min` | 0.20 | 机械臂近距离死区 (m) |
| `arm_reach_max` | 0.60 | 机械臂最大工作半径 (m) |
| `candidate_radius_count` | 3 | 候选圈数 |
| `candidate_angle_step` | 30.0 | 每圈角度步长 (度) |
| `base_link_z` | 0.054 | 机械臂安装高度 (m) |
| `gripper_z_offset` | 0.267 | 抓取高度偏移 (m) |
| `height_tolerance` | 0.1 | 目标高度容差 (m) |
| `robot_radius` | 0.25 | 底盘占据检查半径 (m) |
| `map_required` | false | 地图未收到时是否拒绝全部候选 |
| `score_distance_weight` | 0.6 | 评分距离权重 |
| `score_heading_weight` | 0.4 | 评分朝向权重 |
| `ideal_reach_ratio` | 0.7 | 理想距离占臂展比例 |
| `reach_sigma` | 0.1 | 距离高斯评分标准差 (m) |
