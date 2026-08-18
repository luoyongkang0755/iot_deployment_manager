# iot_deployment 端到端验收结果

## 验收日期
2026-08-04

## 第一轮验收

### 设备最终位置
```
Model: [122]
  - Name: iot_device
  - Pose [ XYZ (m) ] [ RPY (rad) ]:
    [3.099820 -3.119330 0.500000]
    [0.000000 0.000002 -1.704890]
```

### 完整流程日志
```
[amcl-10] [INFO] [1785869328.653596765] [amcl]: initialPoseReceived
[amcl-10] [INFO] [1785869328.653724765] [amcl]: Setting pose (0.000000): 0.000 0.000 0.000
[manipulation_node.py-23] [INFO] [1785869385.288370809] [manipulation_node]: attach: 焊接到 link7 (DetachableJoint)
[manipulation_node.py-23] [INFO] [1785869386.785176705] [manipulation_node]: 移动到 pick_above: [0.0, 2.4, -2.6, 0.0, 2.2, 0.0]
[manipulation_node.py-23] [INFO] [1785869389.839575660] [manipulation_node]: 移动到 carry: [0.0, 0.55, -0.95, 0.0, 0.55, 0.0]
[manipulation_node.py-23] [INFO] [1785869392.894414808] [manipulation_node]: 取货完成，机械臂处于携带位，等待 READY_FOR_MANIPULATION
[deployment_approach_node.py-18] [INFO] [1785869396.891736652] [deployment_approach_node]: 收到新目标: (3.00, -3.00, 0.50)
[deployment_approach_node.py-18] [INFO] [1785869396.894930539] [deployment_approach_node]: 候选统计: 生成 36，可达 32，无碰撞 32
[deployment_approach_node.py-18] [INFO] [1785869396.902995940] [deployment_approach_node]: 尝试候选 1/32: (3.35, -2.80, yaw=-150.0°), score=0.988
[deployment_approach_node.py-18] [INFO] [1785869410.317422539] [deployment_approach_node]: 导航成功，发布 READY_FOR_MANIPULATION
[manipulation_node.py-23] [INFO] [1785869410.325666174] [manipulation_node]: 移动到 place_above: [0.0, 1.05, -1.15, 0.0, 0.5, 0.0]
[manipulation_node.py-23] [INFO] [1785869413.379556070] [manipulation_node]: 移动到 place: [0.0, 1.4, -1.5, 0.0, 1.2, 0.0]
[manipulation_node.py-23] [INFO] [1785869416.435369810] [manipulation_node]: detach: 断开与 link7 的焊接
[manipulation_node.py-23] [INFO] [1785869418.133927463] [manipulation_node]: 夹爪移动到 0.035 m
[manipulation_node.py-23] [INFO] [1785869425.798529142] [manipulation_node]: 放置完成，发布 DEPLOYMENT_COMPLETE
```

### 关键节点状态
- Gazebo 仿真: clock 正常运行
- scout_mini 模型: 正常 spawn
- iot_device 模型: 正常 spawn
- 3 controllers: 全部 active (joint_state_broadcaster, arm_controller, gripper_controller)
- EKF 里程计: /odom 129Hz, frame=odom->base_link
- TF 树: odom->base_link + base_link->全部子 link 完整
- AMCL: 自动初始化 (Setting pose: 0.000 0.000 0.000)
- 导航候选: 1/32 即成功, ~14s 到达

---

## 第二轮验收

### 设备最终位置
```
Model: iot_device
  - Pose [ XYZ (m) ] [ RPY (rad) ]:
    [3.076480 -3.027610 0.500000]
```

### 完整流程日志
```
[amcl-10] [INFO] [1785871137.800638030] [amcl]: Setting pose (0.000000): 0.000 0.000 0.000
[deployment_approach_node.py-18] [INFO] [1785871208.653095445] [deployment_approach_node]: 候选统计: 生成 36，可达 32，无碰撞 32
[deployment_approach_node.py-18] [INFO] [1785871208.658287359] [deployment_approach_node]: 尝试候选 1/32: (3.35, -2.80, yaw=-150.0°), score=0.988
[manipulation_node.py-23] [INFO] [1785871209.223692139] [manipulation_node]: 收到 /amcl_pose，AMCL 定位已就绪
[deployment_approach_node.py-18] [INFO] [1785871224.572134965] [deployment_approach_node]: 导航成功，发布 READY_FOR_MANIPULATION
[manipulation_node.py-23] [INFO] [1785871224.579939919] [manipulation_node]: 放置流程开始
[manipulation_node.py-23] [INFO] [1785871224.580792583] [manipulation_node]: 移动到 place_above: [0.0, 1.05, -1.15, 0.0, 0.5, 0.0]
[manipulation_node.py-23] [INFO] [1785871228.035713888] [manipulation_node]: 移动到 place: [0.0, 1.4, -1.5, 0.0, 1.2, 0.0]
[manipulation_node.py-23] [INFO] [1785871231.441809597] [manipulation_node]: detach: 断开与 link7 的焊接
[manipulation_node.py-23] [INFO] [1785871233.077493437] [manipulation_node]: 夹爪移动到 0.035 m
[ign gazebo-1] [Dbg] [DetachableJoint.cc:351] Removing entity: 127
[ign gazebo-1] [Dbg] [Physics.cc:1757] Detaching joint [127]
[manipulation_node.py-23] [INFO] [1785871234.781201776] [manipulation_node]: 移动到 place_above: [0.0, 1.05, -1.15, 0.0, 0.5, 0.0]
[manipulation_node.py-23] [INFO] [1785871240.889600233] [manipulation_node]: 放置完成，发布 DEPLOYMENT_COMPLETE
```

### 关键节点状态
- 同第一轮，全部正常

---

## 总结

| 轮次 | 设备最终位置 | 目标台面 | 偏差 | 状态 |
|------|-------------|----------|------|------|
| 第一轮 | (3.100, -3.119, 0.500) | (3.00, -3.00, 0.50) | ~0.15m | DEPLOYMENT_COMPLETE |
| 第二轮 | (3.076, -3.028, 0.500) | (3.00, -3.00, 0.50) | ~0.08m | DEPLOYMENT_COMPLETE |

两轮端到端验收均完全通过:
- 取货 -> 导航 -> 放置 -> 设备落地台面 -> DEPLOYMENT_COMPLETE
