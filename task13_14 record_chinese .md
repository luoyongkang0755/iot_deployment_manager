# Scout Mini 双激光雷达仿真问题排查日志

## 问题描述

在使用Nav2导航时，ROS端无法接收到激光雷达数据，`ros2 topic echo /front/scan` 和 `ign topic -e -t /front/scan` 均无数据输出。

## 排查过程

### 第一阶段：基础配置检查

#### 1. QoS配置问题
**问题**：Gazebo使用BestEffort QoS，ROS默认使用Reliable QoS，导致数据无法传递。

**尝试方案**：
- 在launch文件的ros_gz_bridge中添加`qos_sensor_data: True`参数
- 尝试使用`--ros-args`传递QoS参数（失败，参数传递方式错误）

**结果**：QoS配置一致，但问题未解决。

#### 2. 环境变量设置顺序问题
**问题**：`GZ_SIM_RESOURCE_PATH`在Gazebo启动之后设置，导致Gazebo无法找到模型资源。

**解决方案**：将环境变量设置移到Gazebo启动之前。

**修改位置**：`scout_mini_gazebo.launch.py`

**结果**：修复后Gazebo能正常加载模型文件。

#### 3. World文件缺少传感器系统
**问题**：World文件缺少`sensors-system`插件，导致传感器无法初始化。

**解决方案**：在world文件的`<world name="simple_test_world">`标签内添加：
```xml
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
    <rendering>true</rendering>
    <sensor_update_rate>10</sensor_update_rate>
</plugin>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"></plugin>
<plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"></plugin>
```

**结果**：传感器系统成功加载，`ign topic -l`能看到`/front/scan`和`/rear/scan`话题。

#### 4. Gazebo资源路径配置错误
**问题**：资源路径设置不正确，Gazebo无法找到`model://scout_description/meshes/base_link.dae`。

**错误配置**：
```python
gz_resource_path = pkg_scout_description + '/meshes:' + pkg_scout_gazebo + '/worlds'
# 结果：/ws/install/scout_description/share/scout_description/meshes (错误)
```

**正确配置**：
```python
scout_description_parent = os.path.dirname(pkg_scout_description)
gz_resource_path = scout_description_parent + ':' + pkg_scout_gazebo + '/worlds'
# 结果：/ws/install/scout_description/share (正确)
```

**结果**：Gazebo能正确加载3D模型文件，GUI中能看到机器人模型和彩色障碍物。

#### 5. Python导入错误
**问题**：在函数内部导入`os`模块导致`UnboundLocalError`。

**解决方案**：在文件顶部导入`import os`。

**结果**：Launch文件能正常加载。

#### 6. 添加障碍物测试
**问题**：机器人周围空旷，无法验证传感器是否正常工作。

**解决方案**：在world文件中添加4个障碍物箱子：
- obstacle_box_1: 前方 2.0m
- obstacle_box_2: 左侧 2.0m
- obstacle_box_3: 右侧 2.0m
- obstacle_box_4: 后方 2.0m

**结果**：Gazebo GUI中能看到彩色方块，但传感器仍无数据。

### 第二阶段：深度诊断

#### 7. Gazebo版本兼容性检查
**发现**：系统使用的是Ignition/Gazebo Sim，不是经典Gazebo。

**诊断命令**：
```bash
ign topic -i -t /front/scan  # 查看话题信息
ign topic -e -t /world/simple_test_world/stats -n 1  # 查看仿真状态
```

**结果**：
- 话题存在：`tcp://172.17.0.1:41449, ignition.msgs.LaserScan`
- 仿真正在运行：`sim_time: 203秒, iterations: 203682`
- **但是话题没有数据发布！**

### 第三阶段：根本原因定位

#### 8. 传感器类型配置错误
**根本原因**：URDF中`<gazebo>`标签内的传感器类型配置不正确。

**错误配置**：
```xml
<gazebo reference="front_lidar_link">
    <sensor type="ray" name="front_lidar_sensor">  <!-- 错误：ray -->
        ...
    </sensor>
</gazebo>
```

**正确配置**：
```xml
<gazebo reference="front_lidar_link">
    <sensor type="gpu_ray" name="front_lidar_sensor">  <!-- 正确：gpu_ray -->
        ...
    </sensor>
</gazebo>
```

**差异说明**：
- `ray` - CPU ray sensor（经典Gazebo使用）
- `gpu_ray` - GPU ray sensor（Gazebo Sim/Ignition使用）

**修改位置**：`src/external/scout_ros2/scout_description/urdf/scout_mini.xacro`

**修改内容**：
```bash
# 修改前
<sensor type="ray" name="front_lidar_sensor">
<sensor type="ray" name="rear_lidar_sensor">

# 修改后
<sensor type="gpu_ray" name="front_lidar_sensor">
<sensor type="gpu_ray" name="rear_lidar_sensor">
```

**结果**：✅ 成功！激光雷达数据正常发布：
- Gazebo端：`ign topic -e -t /front/scan -n 1` 有数据输出
- ROS端：`ros2 topic echo /front/scan --qos-profile sensor_data --once` 有数据输出
- 数据频率：约10Hz

### 第四阶段：RViz激光显示问题

#### 9. 仿真时间未对齐
**问题**：Gazebo使用仿真时间（/clock话题），但RViz默认使用系统时间，导致TF查询失败。

**错误日志**：
```
[rviz2]: Message Filter dropping message: frame 'scout_mini/base_link/front_lidar_sensor' at time 2427.900 for reason 'discarding message because the queue is full'
```

**解决方案**：为RViz节点添加`use_sim_time`参数：
```python
rviz_node = Node(
    package='rviz2',
    executable='rviz2',
    name='rviz2',
    arguments=['-d', rviz_config],
    parameters=[{'use_sim_time': use_sim_time}],  # 新增
    output='screen')
```

**结果**：部分修复，但RViz仍无法显示激光点云。

#### 10. Frame ID不匹配问题
**问题**：
- 激光数据的frame_id是：`scout_mini/base_link/front_lidar_sensor`（Gazebo自动添加模型名称前缀）
- TF树中的frame是：`front_lidar_link`（URDF定义）
- 两者不匹配，导致RViz无法找到坐标系变换

**错误日志**：
```
[rviz2]: Message Filter dropping message: frame 'scout_mini/base_link/front_lidar_sensor' at time 2427.900 for reason 'discarding message because the queue is full'
```

**诊断过程**：
```bash
# 检查TF树
ros2 run tf2_tools view_frames
# 结果：TF树中没有 scout_mini/base_link/front_lidar_sensor

# 检查激光数据frame_id
ros2 topic echo /front/scan --qos-profile sensor_data --once
# 结果：header.frame_id = "scout_mini/base_link/front_lidar_sensor"
```

**解决方案**：添加静态TF变换，将Gazebo的frame映射到URDF的frame：
```python
# 静态TF publisher - maps Gazebo sensor frame to URDF frame
# Gazebo automatically adds model name prefix to sensor frame_id
# Laser data is in frame: scout_mini/base_link/front_lidar_sensor
# URDF frame is: front_lidar_link
# Transform from sensor frame to URDF frame
front_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='front_lidar_static_tf',
    arguments=[
        '0.245', '0', '0.14',  # xyz (position of sensor relative to base_link)
        '0', '0', '0',         # rpy
        'front_lidar_link',                    # parent frame (URDF frame)
        'scout_mini/base_link/front_lidar_sensor'  # child frame (Gazebo frame)
    ]
)

# Static TF publisher for rear lidar
rear_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    name='rear_lidar_static_tf',
    arguments=[
        '-0.245', '0', '0.14',  # xyz (position of sensor relative to base_link)
        '0', '0', '0',          # rpy
        'rear_lidar_link',                     # parent frame (URDF frame)
        'scout_mini/base_link/rear_lidar_sensor'  # child frame (Gazebo frame)
    ]
)
```

**TF链**：
```
base_link 
  └── front_lidar_link
        └── scout_mini/base_link/front_lidar_sensor (激光数据frame)
```

**结果**：✅ 成功！RViz能正常显示激光点云：
- Fixed Frame设置为`base_link`
- LaserScan话题设置为`/front/scan`或`/rear/scan`
- 激光点云正确显示在机器人周围

## 最终结果
✅ **完全成功！**

- ✅ Gazebo端激光数据正常发布（约10Hz）
- ✅ ROS端接收到激光数据
- ✅ RViz中正确显示激光点云
- ✅ 激光点云与障碍物位置匹配

## 修改文件清单

1. **scout_mini_gazebo.launch.py**
   - 修改：环境变量设置顺序（移到Gazebo启动之前）
   - 修改：Gazebo资源路径配置（使用父目录）
   - 修改：RViz节点添加`use_sim_time`参数
   - 添加：Python os模块导入
   - 添加：front_lidar_static_tf节点
   - 添加：rear_lidar_static_tf节点

2. **simple_test_world.world**
   - 添加：sensors-system插件
   - 添加：scene-broadcaster-system插件
   - 添加：user-commands-system插件
   - 添加：4个障碍物箱子
   - 升级：SDF版本从1.6到1.8

3. **scout_mini.xacro**
   - 修改：前激光雷达传感器类型从`ray`改为`gpu_ray`
   - 修改：后激光雷达传感器类型从`ray`改为`gpu_ray`
   - 确认：添加`<always_on>true</always_on>`配置

## 经验总结

### Gazebo仿真环境配置
1. **Gazebo Sim vs 经典Gazebo**：不同版本的Gazebo使用不同的传感器类型名称
   - 经典Gazebo使用 `ray`
   - Gazebo Sim/Ignition使用 `gpu_ray`

2. **环境变量顺序**：必须在Gazebo启动之前设置资源路径
   - `GZ_SIM_RESOURCE_PATH`
   - `IGN_GAZEBO_RESOURCE_PATH`
   - `GAZEBO_MODEL_PATH`

3. **World文件完整性**：必须包含所有必要的系统插件
   - sensors-system：传感器处理
   - scene-broadcaster-system：场景广播
   - user-commands-system：用户命令

4. **资源路径格式**：Gazebo的`model://` URI需要正确的目录结构
   - 需要指向包含`模型名称/子目录`的父目录
   - 不是直接指向`meshes`目录

### ROS2与Gazebo桥接
5. **QoS配置**：传感器数据通常使用BestEffort策略
   - 使用`qos_sensor_data: True`参数

6. **仿真时间同步**：所有节点应使用相同的时钟源
   - 使用`use_sim_time`参数确保时间一致

7. **Frame ID映射**：Gazebo自动为传感器frame添加模型名称前缀
   - 需要通过静态TF建立映射关系
   - 或在RViz中手动设置Fixed Frame为完整的Gazebo frame

### TF树维护
8. **静态TF方向**：TF变换的方向很重要
   - parent_frame → child_frame
   - 对于Gazebo传感器：sensor_frame → URDF_frame

9. **坐标系位置**：确保TF变换的位置与URDF中的joint位置一致
   - front_lidar: x=0.245, y=0, z=0.14
   - rear_lidar: x=-0.245, y=0, z=0.14

## 测试验证命令

```bash
# 重新构建
cd /home/luoyongkang/scout_nav2_mini
colcon build --symlink-install

# 运行launch文件
source install/setup.bash
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 测试Gazebo端激光数据
ign topic -e -t /front/scan -n 1

# 测试ROS端激光数据
ros2 topic echo /front/scan --qos-profile sensor_data --once

# 检查数据频率
ros2 topic hz /front/scan

# 检查TF树
ros2 run tf2_tools view_frames

# 检查TF变换
ros2 run tf2_ros tf2_echo base_link front_lidar_link
```

## RViz配置步骤

1. 添加LaserScan显示
   - 点击"Add" → "By topic" → 选择"/front/scan"

2. 设置Fixed Frame
   - 设置为 `base_link`

3. 调整显示参数
   - Size (m): 0.1
   - Style: Points
   - Queue Size: 10

## 日期
2026-06-09 ~ 2026-06-10
