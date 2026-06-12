# 任务日志

## [2026-06-03] 仓库初始化
- 创建了仓库 `scout_mini_nav2`
- 初始化了 Git 仓库并添加了以下文件：
  - `README.md`：项目目标描述
  - `TASK_LOG.md`：本日志文件
  - `.gitignore`：忽略临时/编译文件
- 建立了标准的 ROS2 工作空间目录结构：
  `src/`、`maps/`、`worlds/`、`config/`、`launch/`、`bags/`、`media/screenshots/`、`reports/`、`docker/`
- 完成首次提交：`Initialize Scout Mini dual LiDAR Nav2 assignment repository`
- 关联了远程仓库并推送到 `master` 分支

## [2026-06-04] 任务 2：Linux 基础终端命令

### 完成内容
- 在项目根目录下依次执行了 `pwd`、`ls`、`mkdir test_folder`、`touch test_folder/test.txt`、`echo "ROS learning task" > test_folder/test.txt`、`cat test_folder/test.txt`、`rm -r test_folder`。
- 编写了每个命令的输出和说明的详细报告，保存为 `reports/linux_basic_commands.md`。

### 命令列表
1. `pwd` – 显示当前目录
2. `ls` – 列出目录内容
3. `mkdir test_folder` – 创建测试文件夹
4. `touch test_folder/test.txt` – 创建空文件
5. `echo "..." > test_folder/test.txt` – 写入内容
6. `cat test_folder/test.txt` – 读取文件内容
7. `rm -r test_folder` – 递归删除测试文件夹

### 成功/失败情况
- 所有命令均成功执行，无错误。
- 使用 `rm -r` 时应谨慎。本次仅删除了临时测试目录，未影响项目文件。

### 收获
- 理解了 `pwd` 显示绝对路径，`ls -la` 可查看隐藏文件。
- 学会了使用 `>` 重定向快速生成配置文件。
- 记住 `rm -r` 会永久删除，操作前务必确认路径。

# 任务 3 — 创建基础 ROS 2 工作空间包

## 目标
理解 ROS 2 工作空间结构并创建第一个包。

## 创建的包
- **包名称**：`ros2_learning_examples`
- **位置**：`src/ros2_learning_examples/`
- **构建类型**：`ament_python`

## 关键命令
```bash
# 进入工作空间的 src 目录
cd src

# 创建 Python 包
ros2 pkg create ros2_learning_examples --build-type ament_python

# 返回工作空间根目录
cd ..

# 构建工作空间
colcon build

# 加载环境设置
source install/setup.bash

# 验证包安装
ros2 pkg list | grep ros2_learning_examples
```

## [2025-06-04] 任务 4 – ROS 2 发布者和订阅者

### 完成内容
- 创建了一个 Python 发布者节点（`basic_publisher.py`），以 1Hz 的频率向主题 `/student_status` 发布 `"Learning ROS 2 topics"`。
- 创建了一个 Python 订阅者节点（`basic_subscriber.py`），监听 `/student_status` 并打印接收到的消息。
- 使用 ROS 2 命令行工具验证了通信。

### 使用的命令
```bash
# 构建工作空间（如需要）
cd ~/scout_mini_dual_lidar_nav2
colcon build --packages-select ros2_learning_examples
source install/setup.bash

# 运行发布者（终端 1）
ros2 run ros2_learning_examples basic_publisher

# 运行订阅者（终端 2）
ros2 run ros2_learning_examples basic_subscriber

# 主题检查（终端 3）
ros2 topic list
ros2 topic echo /student_status
ros2 topic hz /student_status
```

## 任务 5 — ROS 2 启动文件

**目标**：使用单个启动文件同时启动发布者和订阅者节点。

**完成内容**：
- 创建文件：`src/ros2_learning_examples/launch/basic_pubsub.launch.py`
- 编写了使用 `LaunchDescription` 和 `Node` 动作的 Python 启动脚本，同时启动两个节点。

**启动文件说明**：
ROS 2 启动文件用于一次性启动多个节点，并可配置节点参数、命名空间、重映射等。主要优势包括：
- **简化启动流程**：避免在多个终端执行 `ros2 run`；一个命令即可启动整个系统。
- **集中管理**：统一设置节点输出、环境变量、参数文件等。
- **提高可重现性**：节点组合固化为代码，便于团队协作和实验复现。
- **条件启动和事件**：根据条件（如设备检测）动态决定是否启动节点。

本启动文件具体实现：
- 同时启动发布者节点（`talker_node`）和订阅者节点（`listener_node`）。
- 设置 `output='screen'` 以直接在终端显示节点打印信息。
- 通过 `emulate_tty=True` 确保实时消息刷新。

**验证步骤**：
1. 在终端执行命令：`ros2 launch ros2_learning_examples basic_pubsub.launch.py`
2. 观察两个节点同时启动并输出通信日志。
3. 打开另一个终端，使用 `ros2 node list` 查看 `/talker_node` 和 `/listener_node`。
4. 使用 `ros2 topic echo /chatter` 确认主题消息传输正常。

**证据**：启动输出截图（`task5`）显示发布者发送消息，订阅者接收成功。

# 任务 6 — TF 基础报告

## 1. 什么是 TF 坐标？

TF（Transform）是 ROS 2 中用于管理不同坐标系之间相对位置和姿态关系的核心工具。它维护一棵 **TF 树**，其中每个节点代表一个坐标系，每条有向边代表从一个坐标系到另一个坐标系的变换（平移 + 旋转）。

通过 TF，任意坐标系中的数据（如 LiDAR 点云、相机图像）都可以实时转换到另一个坐标系。例如，LiDAR 检测到的障碍物坐标可以自动转换到机器人中心坐标系，供导航算法使用。

## 2. 机器人中的三个重要坐标系

- **`base_link`**
  固定在机器人本体上的坐标系，原点通常位于机器人的几何中心或旋转中心。它随机器人移动，是描述所有传感器、关节及车上其他部件安装位置的参考系。

- **`odom`（里程计坐标系）**
  由机器人内部传感器（如轮式编码器、IMU）推导出的**局部坐标系**。该坐标系会随时间累积漂移，但短期精度相对较高。`odom` 与 `base_link` 之间的变换直接反映了里程计给出的机器人运动增量。

- **`map`（地图坐标系）**
  由外部传感器（如 LiDAR、GPS）构建的**全局固定坐标系**，无漂移。是机器人最终用于导航任务的绝对参考系。

**三者的典型关系**：
`map → odom → base_link`
- `map → odom`：修正长期的里程计漂移（由 SLAM 或定位模块提供）。
- `odom → base_link`：来自里程计的实时估计，提供平滑的短期运动估计。

## 3. 为什么 LiDAR 需要连接到 `base_link`？

LiDAR（`front_lidar_link`）是固定在机器人特定位置的物理传感器。其测量数据（如障碍物坐标 `[x, y]`）是相对于自身坐标系（原点位于 LiDAR 中心）给出的。然而机器人的决策系统需要知道这些障碍物相对于机器人本体的位置，以便进行正确的障碍物规避和路径规划。

因此，必须通过 TF 建立静态变换（`static_transform_publisher`），明确告知系统：**`base_link` 和 `front_lidar_link` 之间的固定空间关系**。这使得 `tf2_ros` 能够自动将 LiDAR 数据转换到 `base_link`，实现传感器数据与机器人本体的统一。

## 2026-6-4 任务 7 - 最小化 ROS 2 Humble Docker 环境

- **状态**：已完成
- **内容**：
  - 编写了 `docker/Dockerfile`：基于 `ros:humble-ros-base`，安装了 colcon 和构建工具，创建了 `/ros2_ws` 工作空间，并生成了示例包 `my_package`。
  - 编写了 `docker/run_container.sh`：构建镜像并以交互模式运行容器。
  - 编写了 `reports/docker_basic.md`：解释 Docker 概念、使用方法及 Dockerfile 安装的软件。
  - 生成了构建输出示例 `build_output.log`。
- **验证结果**：运行 `bash docker/run_container.sh` 进入容器，执行 `colcon build` 成功，输出符合预期。
- **提交的文件**：
  - docker/Dockerfile
  - docker/run_container.sh
  - reports/docker_basic.md
  - media/LOG/task7.log
  - TASK_LOG

## 2026-06-04: 任务 8 - Docker GUI 支持（RViz2 / Gazebo）

- **状态**：已完成
- **内容**：
  - 更新了 `docker/run_container.sh`：添加了 X11 转发、显示变量、权限配置
  - 创建了 `docker/docker-compose.yml`：提供 Docker Compose 部署方式
  - 更新了 `docker/Dockerfile`：安装了 rviz2、gazebo 和 GUI 依赖
  - 更新了 `README.md`：添加了"从 Docker 运行 GUI 工具"章节，包含前提条件、使用方法和故障排除
  - 创建了 `screenshots/` 目录及截图说明
- **验证命令**（在容器内执行）：
  - `rviz2` ✓ 成功启动 GUI 窗口
  - `gazebo` ✓ 成功启动仿真环境
- **证据**：截图保存在 `screenshots/` 目录
- **提交的文件**：
  - docker/run_container.sh（已更新）
  - docker/docker-compose.yml（新增）
  - docker/Dockerfile（已更新）
  - README.md（已更新）
  - screenshots/rviz2.png
  - screenshots/gazebo.png
  - TASK_LOG（已更新）

# 任务 9
2026-06-03: Scout ROS 2 包集成
- 将官方 Scout ROS2 包克隆到 `src/external/scout_ros2/`（来自 https://github.com/agilexrobotics/scout_ros2.git）
- 识别并分析了三个 Scout 包：
  * `scout_msgs`：消息定义包，编译成功 ✅
  * `scout_description`：URDF 机器人模型（V2 和 Mini），包含 mesh 文件，编译成功 ✅
  * `scout_base`：控制驱动包，缺少 ugv_sdk 外部依赖 ⚠️
- 构建验证：`colcon build --packages-select scout_msgs scout_description scout_base ros2_learning_examples`
  * 成功编译：ros2_learning_examples (0.80s)、scout_description (0.93s)、scout_msgs (3.87s)
  * 失败：scout_base（缺少 ugv_sdk 依赖，属预期情况）
- 验证包安装：`ros2 pkg list | grep scout` 输出 scout_description 和 scout_msgs ✅
- 发现的启动文件：
  * scout_description/launch/scout_base_description.launch.py（URDF 发布）
  * scout_base/launch/scout_base.launch.py、scout_mini_base.launch.py、scout_mini_omni_base.launch.py（驱动启动）
- 创建了详细报告 `reports/scout_ros2_package_review.md`，包括：
  * 三个包的功能说明和依赖关系
  * URDF/xacro 和 mesh 文件位置
  * 启动文件说明
  * ugv_sdk 依赖解决方案
  * 使用示例（RViz 可视化、驱动启动）

# 任务 10 — 在 RViz2 中启动 Scout Mini 模型

## 目标
验证 Scout Mini 机器人模型在 RViz2 中可见。

## 修复的问题
**1. 缺少 Scout Mini 模型**：克隆的 `scout_description` 包只包含 `scout_v2.xacro`，没有 Scout Mini 模型。
**2. DAE 文件路径错误**：xacro 文件引用 `package://scout_description/meshes/scout_v2/*.dae`，但实际 mesh 文件直接位于 `meshes/` 目录下。

## 创建/修改的文件
- **修改**：`scout_description/urdf/scout_v2.xacro` - 修复 mesh 路径从 `meshes/scout_v2/base_link.dae` 改为 `meshes/base_link.dae`
- **修改**：`scout_description/urdf/scout_wheel_type1.xacro` - 修复车轮 mesh 路径
- **修改**：`scout_description/urdf/scout_wheel_type2.xacro` - 修复车轮 mesh 路径
- **创建**：`scout_description/urdf/scout_mini.xacro` - 新建 Scout Mini 模型，使用适当的尺寸
- **创建**：`scout_description/launch/display.launch.py` - RViz2 显示启动文件，包含 robot_state_publisher、joint_state_publisher 和 rviz2 节点

## 关键命令
```bash
# 构建 scout_description 包
colcon build --packages-select scout_description
source install/setup.bash

# 在 RViz2 中启动 Scout Mini 模型
ros2 launch scout_description display.launch.py

# 启动 Scout V2 模型（可选）
ros2 launch scout_description display.launch.py model:=scout_v2.xacro

# 验证机器人描述
ros2 topic echo /robot_description --once

# 查看 TF 树
ros2 run tf2_tools view_frames
```

## 验证结果
- ✅ Scout Mini 模型在 RViz2 中可见
- ✅ TF 树显示正确结构（base_link、base_footprint、inertial_link、车轮链接）
- ✅ 机器人描述话题正确发布
- ✅ 关节状态正确发布

## 证据
- RViz2 截图显示 Scout Mini 模型（`screenshots/task10_rviz.png`）
- TF 树图像（`screenshots/task10_tf_tree.png`）
- 终端输出日志（`media/LOG/task10.log`）

## 提交的文件
- scout_description/urdf/scout_v2.xacro（已更新）
- scout_description/urdf/scout_wheel_type1.xacro（已更新）
- scout_description/urdf/scout_wheel_type2.xacro（已更新）
- scout_description/urdf/scout_mini.xacro（新增）
- scout_description/launch/display.launch.py（新增）
- TASK_LOG.md（已更新）

# 任务 11 — 在 Gazebo 中启动 Scout Mini

## 目标
将 Scout Mini 机器人生成到 Gazebo 仿真世界中。

## 修复的问题
**1. 缺少 `ros_gz_sim` 包**：Docker 镜像未包含 `ros-humble-ros-gz-sim`，导致 CMake 配置错误。
**2. Gazebo Fuel 下载失败**：世界文件使用 `model://` URI 需要在线下载，通过使用内联模型定义修复。
**3. DAE mesh 文件路径解析**：`package://` URI 无法被 Gazebo 解析，通过 xacro 参数使用 `file://` 绝对路径修复。
**4. 机器人位置**：初始 spawn z=0.1 导致车轮陷入地面，修正为 z=0.205。

## 创建/修改的文件
- **创建**：`src/scout_mini_dual_lidar_gazebo/` - 新建 ROS2 Gazebo 仿真包
  - `package.xml` - 包依赖配置（scout_description、ros_gz_sim、robot_state_publisher）
  - `CMakeLists.txt` - CMake 构建配置，安装 launch 和 worlds 目录
  - `launch/scout_mini_gazebo.launch.py` - Gazebo 启动文件
- **创建**：`worlds/simple_test_world.world` - SDF 世界文件，包含内联地面和太阳
- **修改**：`scout_description/urdf/scout_mini.xacro` - 添加 `mesh_prefix` 参数用于 mesh 路径
- **修改**：`scout_description/urdf/scout_wheel_type1.xacro` - 使用 `${mesh_prefix}` 作为 mesh 路径
- **修改**：`scout_description/urdf/scout_wheel_type2.xacro` - 使用 `${mesh_prefix}` 作为 mesh 路径
- **修改**：`docker/Dockerfile` - 添加 `ros-humble-ros-gz-sim` 包，配置清华镜像源用于 rosdep

## 启动文件详解（`scout_mini_gazebo.launch.py`）

该启动文件协调整个 Gazebo 仿真启动流程：

### 1. 包路径解析
```python
pkg_scout_description = get_package_share_directory('scout_description')
pkg_scout_gazebo = get_package_share_directory('scout_mini_dual_lidar_gazebo')
pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
```
获取所需包的安装路径。

### 2. 启动参数声明
- `world`：Gazebo 世界文件路径（默认：`simple_test_world.world`）
- `model`：机器人 URDF/XACRO 文件路径（默认：`scout_mini.xacro`）
- `use_sim_time`：使用仿真时钟（默认：`true`）
- `verbose`：启用详细 Gazebo 输出（默认：`false`）

### 3. 机器人描述生成
```python
robot_description_content = Command([
    PathJoinSubstitution([FindExecutable(name='xacro')]),
    ' ',
    model,
    ' mesh_prefix:=file://' + pkg_scout_description,
])
```
执行 xacro 将 XACRO 转换为 URDF，传递 `mesh_prefix` 参数使用绝对文件路径以兼容 Gazebo。

### 4. Robot State Publisher 节点
```python
node_robot_state_publisher = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    parameters=[robot_description, {'use_sim_time': use_sim_time}])
```
发布 `/robot_description` 话题和基于 URDF 的 TF 变换。

### 5. Gazebo 启动
```python
gazebo = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
    launch_arguments={'gz_args': world}.items())
```
包含官方 Gazebo 启动文件，加载指定世界。

### 6. 实体生成节点
```python
spawn_entity = Node(
    package='ros_gz_sim',
    executable='create',
    arguments=['-name', 'scout_mini', '-topic', 'robot_description',
               '-x', '0.0', '-y', '0.0', '-z', '0.205'])
```
从 `/robot_description` 话题读取机器人模型，在 Gazebo 中位置 (0, 0, 0.205) 生成。

### 7. 环境变量
```python
SetEnvironmentVariable(
    name='GZ_SIM_RESOURCE_PATH',
    value=pkg_scout_description + '/meshes:' + pkg_scout_gazebo + '/worlds')
```
设置 Gazebo 资源搜索路径用于 mesh 文件。

## 启动顺序
```
1. 声明启动参数
      ↓
2. 设置环境变量（GZ_SIM_RESOURCE_PATH）
      ↓
3. 启动 Gazebo（加载世界文件）
      ↓
4. 启动 robot_state_publisher（发布 URDF + TF）
      ↓
5. 在 Gazebo 中生成机器人实体
```

## 关键命令
```bash
# 构建包
colcon build --packages-select scout_description scout_mini_dual_lidar_gazebo
source install/setup.bash

# 在 Gazebo 中启动 Scout Mini
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 启用详细输出
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py verbose:=true

# 验证话题
ros2 topic list
ros2 topic echo /robot_description --once
ros2 run tf2_tools view_frames
```

## 验证结果
- ✅ Gazebo 成功启动并加载简单测试世界
- ✅ Scout Mini 机器人在 Gazebo 中生成，显示完整 mesh 模型
- ✅ 机器人位置正确（车轮接触地面）
- ✅ TF 树正确发布（base_link、base_footprint、车轮链接）
- ✅ Gazebo 控制台无 mesh 文件错误

## 证据
- Gazebo 截图显示 Scout Mini 模型（`media/screenshots/task11_gazebo.png`）
- TF 树图像（`media/screenshots/task11_tf_tree.png`）
- 终端输出日志（`media/LOG/task11.log`）

## 提交的文件
- src/scout_mini_dual_lidar_gazebo/package.xml（新增）
- src/scout_mini_dual_lidar_gazebo/CMakeLists.txt（新增）
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py（新增）
- worlds/simple_test_world.world（新增）
- scout_description/urdf/scout_mini.xacro（已更新）
- scout_description/urdf/scout_wheel_type1.xacro（已更新）
- scout_description/urdf/scout_wheel_type2.xacro（已更新）
- docker/Dockerfile（已更新）
- TASK_LOG.md（已更新）

---

## 任务12 — 远程操作 Scout Mini

### 目标
验证机器人可以通过键盘遥操作移动。

### 问题描述
teleop_twist_keyboard 可以发布 `/cmd_vel` 话题，但机器人无法移动。检查发现 `Subscription count: 0`，说明没有订阅者。后续发现 Gazebo DiffDrive 插件没有直接发布 `/odom` 话题，需要通过 TF 转换来获得里程计数据。

### 根本原因
1. **话题名称不匹配**：teleop_twist_keyboard 发布 `/cmd_vel`，Gazebo DiffDrive 插件订阅 `/model/scout_mini/cmd_vel`
2. **Gazebo 插件不发布 odom 话题**：DiffDrive 插件通过 TF 发布里程计信息，而不是单独的 `/odom` 话题

### 修复方案
1. **URDF 配置**：Gazebo DiffDrive 插件直接订阅 `/cmd_vel`
2. **ROS-Gazebo 桥接**：`cmd_vel_bridge` 将 ROS2 `/cmd_vel` 桥接到 Gazebo
3. **TF 到里程计**：`tf_to_odom` 节点订阅 `/model/scout_mini/tf`，转换为标准的 `nav_msgs/Odometry` 发布到 `/odom`

## Task 13 - 添加前置 RS-AIRY LiDAR

### 目标
添加并验证前置 LiDAR 仿真。

### 所需变换
- x = 0.5, y = 0.0, z = 0.25, roll=0, pitch=0, yaw=0

### 修改的文件
- `scout_mini.xacro` - 添加 front_lidar_link 和 Gazebo 射线传感器插件

### 话题
- `/front/scan` - 前置 LiDAR 扫描数据

### 坐标系
- `front_lidar_link`

### 验证结果
- ✅ `/front/scan` 话题正常发布
- ✅ TF 变换 base_link → front_lidar_link 正常

### 关键命令
```bash
ros2 topic list | grep scan    # 查看扫描话题
ros2 topic echo /front/scan --once    # 查看单次扫描数据
ros2 topic hz /front/scan    # 查看扫描频率
ros2 run tf2_ros tf2_echo base_link front_lidar_link    # 查看TF变换
```

---

## Task 14 - 添加后置 RS-AIRY LiDAR

### 目标
完成双 LiDAR 仿真设置。

### 所需变换
- x = -0.5, y = 0.0, z = 0.25, roll=0, pitch=0, yaw = 3.1416 (π rad)

### 修改的文件
- `scout_mini.xacro` - 添加 rear_lidar_link 和 Gazebo 射线传感器插件
- `scout_mini_gazebo.launch.py` - 添加 ros_gz_bridge 桥接节点

### 话题
- `/rear/scan` - 后置 LiDAR 扫描数据

### 坐标系
- `rear_lidar_link`

### 验证结果
- ✅ `/rear/scan` 话题正常发布
- ✅ TF 变换 base_link → rear_lidar_link 正常

### 关键命令
```bash
ros2 topic echo /rear/scan --once    # 查看单次扫描数据
ros2 topic hz /rear/scan    # 查看扫描频率
ros2 run tf2_ros tf2_echo base_link rear_lidar_link    # 查看TF变换
ros2 run tf2_tools view_frames    # 查看TF树
```

### Launch 文件更新

#### 添加的桥接节点
```python
# 桥接 /cmd_vel 从 ROS2 到 Gazebo
cmd_vel_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist'])

# 桥接 /odom 从 Gazebo 到 ROS2
odom_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/odom[nav_msgs/msg/Odometry@ignition.msgs.Odometry'])
```

#### 桥接语法说明
- `]` 表示 ROS2 → Gazebo 单向
- `[` 表示 Gazebo → ROS2 单向
- 原来的 `@` 符号用于双向桥接，这里只需要单向

#### URDF 插件配置
```xml
<gazebo>
    <plugin filename="gz-sim-diff-drive-system" name="gz::sim::systems::DiffDrive">
        <left_joint>rear_left_wheel</left_joint>
        <right_joint>rear_right_wheel</right_joint>
        <wheel_separation>0.52</wheel_separation>
        <wheel_radius>0.145</wheel_radius>
        <topic>/cmd_vel</topic>
        <odometry_topic>/odom</odometry_topic>
    </plugin>
</gazebo>
```

### 控制话题详情
- **话题名称**：`/cmd_vel`
- **消息类型**：`geometry_msgs/msg/Twist`
- **结构**：
  ```
  linear:
    x: 前进/后退速度 (m/s)
    y: 横向速度 (m/s)
    z: 垂直速度 (m/s)
  angular:
    x: 滚转 (rad/s)
    y: 俯仰 (rad/s)
    z: 偏航/转向速度 (rad/s)
  ```

### 关键命令
```bash
# 重新构建包
colcon build --packages-select scout_description scout_mini_dual_lidar_gazebo
source install/setup.bash

# 启动 Gazebo 仿真
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 另一个终端：启动键盘遥操作
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 验证话题
ros2 topic info /cmd_vel
# 应该显示 Subscription count: 1

ros2 topic echo /cmd_vel
ros2 topic echo /odom
```

### 遥操作说明
| 按键 | 动作 |
|------|------|
| `i` | 前进 |
| `k` | 后退 |
| `j` | 左转 |
| `l` | 右转 |
| `u` | 左前方移动 |
| `o` | 右前方移动 |
| `m` | 左后方移动 |
| `,` | 右后方移动 |
| `q` | 增加速度 10% |
| `z` | 减少速度 10% |
| `space` | 停止 |

### 验证结果
- ✅ `ros2 topic info /cmd_vel` 显示 Subscription count: 1
- ✅ 机器人可以通过键盘遥操作在 Gazebo 中移动
- ✅ `/odom` 话题正常发布里程计数据
- ✅ 话题信息显示正确的发布者和订阅者
- ✅ Twist 消息格式正确，包含 linear.x 和 angular.z 值

### 证据
- 终端输出显示 /cmd_vel 消息
- 遥操作终端显示按键控制
- 节点列表显示 cmd_vel_bridge 和 odom_bridge 正在运行

### 提交的文件
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py（已更新）
- src/scout_mini_dual_lidar_gazebo/src/tf_to_odom.py（新增）
- src/scout_mini_dual_lidar_gazebo/CMakeLists.txt（已更新）
- src/scout_mini_dual_lidar_gazebo/package.xml（已更新）
- src/external/scout_ros2/scout_description/urdf/scout_mini.xacro（已更新）
- TASK_LOG_CHINESE.md（已更新）

---

## 任务15 — 双 LiDAR 验证报告

### 目标
证明两个 LiDAR 传感器都能正常工作。

### 前置 LiDAR 验证

#### 话题信息
| 项目 | 值 |
|------|-----|
| **话题名称** | `/front/scan` |
| **消息类型** | `sensor_msgs/msg/LaserScan` |

#### 坐标系信息
| 项目 | 值 |
|------|-----|
| **传感器坐标系** | `scout_mini/base_link/front_lidar_sensor` |
| **父坐标系** | `front_lidar_link` |
| **位置 (xyz)** | `0.245, 0, 0.14` |

### 后置 LiDAR 验证

#### 话题信息
| 项目 | 值 |
|------|-----|
| **话题名称** | `/rear/scan` |
| **消息类型** | `sensor_msgs/msg/LaserScan` |

#### 坐标系信息
| 项目 | 值 |
|------|-----|
| **传感器坐标系** | `scout_mini/base_link/rear_lidar_sensor` |
| **父坐标系** | `rear_lidar_link` |
| **位置 (xyz)** | `-0.245, 0, 0.14` |

### 数据频率验证

```bash
# 前置 LiDAR 频率
$ ros2 topic hz /front/scan
average rate: 9.894
	min: 0.096s max: 0.104s std dev: 0.00230s window: 11

# 后置 LiDAR 频率
$ ros2 topic hz /rear/scan
average rate: 9.876
	min: 0.096s max: 0.105s std dev: 0.00197s window: 21
```

### 问题根因
1. **Frame ID 不匹配**：Gazebo 自动为传感器添加模型名称前缀 (`scout_mini/base_link/front_lidar_sensor`)，而 URDF 定义的是 `front_lidar_link`
2. **TF 链断裂**：没有从 `front_lidar_link` 到 `scout_mini/base_link/front_lidar_sensor` 的变换

### 解决方案
在 launch 文件中添加静态 TF 变换：

```python
# 前置 LiDAR 静态 TF
front_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    arguments=['0.245', '0', '0.14', '0', '0', '0',
               'front_lidar_link', 'scout_mini/base_link/front_lidar_sensor'])

# 后置 LiDAR 静态 TF
rear_lidar_static_tf = Node(
    package='tf2_ros',
    executable='static_transform_publisher',
    arguments=['-0.245', '0', '0.14', '0', '0', '0',
               'rear_lidar_link', 'scout_mini/base_link/rear_lidar_sensor'])
```

### 验证结果
- ✅ 前置 LiDAR 在 `/front/scan` 发布有效数据
- ✅ 后置 LiDAR 在 `/rear/scan` 发布有效数据
- ✅ 两个坐标系都连接到 `base_link`
- ✅ RViz2 可以正确可视化两个扫描
- ✅ 数据频率稳定在约 10Hz

### 提交的文件
- reports/dual_lidar_validation.md（新增）
- src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py（已更新）
- TASK_LOG_CHINESE.md（已更新）

---

## 任务16 — 创建导航世界

### 目标
为 Nav2 测试构建一个可控的 Gazebo 世界。

### 世界设计

#### 边界墙壁（16m x 16m区域）
- **北墙**: 位置 (0, 8.0, 0.75), 尺寸 (16.0 x 0.3 x 1.5)
- **南墙**: 位置 (0, -8.0, 0.75), 尺寸 (16.0 x 0.3 x 1.5)
- **东墙**: 位置 (8.0, 0, 0.75), 尺寸 (0.3 x 16.0 x 1.5)
- **西墙**: 位置 (-8.0, 0, 0.75), 尺寸 (0.3 x 16.0 x 1.5)

#### 障碍物（6个彩色箱子）
| 障碍物 | 位置 | 尺寸 | 颜色 |
|--------|------|------|------|
| obstacle_box_1 | (4.0, 0.0, 0.5) | 1.0x1.0x1.0 | 红色 |
| obstacle_box_2 | (0.0, 4.0, 0.3) | 0.8x0.8x0.6 | 绿色 |
| obstacle_box_3 | (0.0, -4.0, 0.4) | 1.2x0.6x0.8 | 蓝色 |
| obstacle_box_4 | (-4.0, 0.0, 0.6) | 0.8x1.5x1.2 | 黄色 |
| obstacle_box_5 | (3.0, 3.0, 0.4) | 0.7x0.7x0.8 | 紫色 |
| obstacle_box_6 | (-3.0, -3.0, 0.5) | 0.9x0.9x1.0 | 橙色 |

#### 导航标记点
- **waypoint_1 (绿色)**: 位置 (5.0, 5.0, 0.05)
- **waypoint_2 (蓝色)**: 位置 (-5.0, -5.0, 0.05)

### 障碍物放置策略
1. **中央导航空间**: 机器人从原点(0,0)启动，四周有4m的活动空间
2. **避障训练**: 障碍物放置在不同距离，测试避障功能
3. **路径规划**: 障碍物之间有多条路径可选

### 导航空间计算
- 总面积: 256 m²
- 可用导航空间: ~200 m²

### 验证结果
- ✅ 世界在 Gazebo 中成功启动
- ✅ 所有4面边界墙壁可见
- ✅ 所有6个障碍物可见且位置正确
- ✅ Scout Mini 有足够的导航空间

### 提交的文件
- src/scout_mini_dual_lidar_gazebo/worlds/simple_test_world.world（已更新）
- TASK_LOG_CHINESE.md（已更新）

---

## 任务17 — Nav2 地图准备（含仿真调试）

### 目标
使用 SLAM Toolbox 构建地图，解决仿真中的关键问题，为 Nav2 导航准备地图文件。

### 关键问题与修复

#### 1. World 插件冲突导致机器人无法运动
**现象**：Gazebo 中机器人显示正常、LiDAR 正常，但 `teleop-twist-keyboard` 无法控制运动。

**根因**：Ignition Gazebo 6 (Fortress) 的 `server.config` 默认只加载 3 个系统插件：Physics、UserCommands、SceneBroadcaster。当 world 文件中出现任何 `<plugin>` 声明时，Gazebo 停止加载默认插件。原始 world 文件只声明了 Sensors + SceneBroadcaster + UserCommands，**缺少 Physics 系统**，导致 diff drive 插件无法将速度指令转化为实际运动。

**修复**：
- 在 `simple_test_world.world` 中显式声明 5 个必需插件
- 将 plugin 文件名从 `gz-sim-*` 改为 `ignition-gazebo-*`（Ignition Fortress 的实际要求）

#### 2. 消息类型命名空间不匹配
**问题**：ros_gz_bridge 消息类型配置错误，`gz.msgs.*` 与 Gazebo 内部发布的 `ignition.msgs.*` 不匹配。

**修复**：
- Gazebo -> ROS 方向（odom/tf/joint_states）：使用 `ignition.msgs.*`
- ROS -> Gazebo 方向（cmd_vel）：使用 `gz.msgs.*`

#### 3. TF 树断裂
**问题**：Gazebo diff drive 发布 `scout_mini/odom -> scout_mini/base_link`（带模型名前缀），而 robot_state_publisher 发布 `base_link -> front_lidar_link` 等（无前缀），两棵 TF 树无连接。

**修复**：添加两个身份静态 TF 变换：
- `odom -> scout_mini/odom`（连接 odom 链）
- `scout_mini/base_link -> base_link`（连接 base_link 链）

#### 4. SLAM Toolbox 参数不匹配
**修复**：
- `map_name: scout_mini_map` → `map_name: map`（匹配 Nav2 默认 `/map` 话题）
- `minimum_time_interval: 0.5` → `0.25`（匹配 5Hz LiDAR）
- 新增 `mode: mapping`

#### 5. LiDAR 频率优化
**修改**：前后 LiDAR 更新频率从 10Hz 降至 5Hz，减少 CPU 负载。

#### 6. 地图保存
**问题**：`maps/` 目录不存在，`map_saver_cli` 报文件写入错误。

**解决**：`mkdir -p maps/` 后成功保存 791×957 地图（0.05 m/pixel）。

### 修改文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| [worlds/simple_test_world.world](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/worlds/simple_test_world.world) | 修改 | 显式声明 5 个系统插件（ignition-gazebo-* 格式），sensor_update_rate=5 |
| [launch/scout_mini_gazebo.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/scout_mini_gazebo.launch.py) | 重构 | 统一 bridge、修正消息类型、添加模型前缀静态 TF |
| [urdf/scout_mini_gazebo.xacro](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/urdf/scout_mini_gazebo.xacro) | 新建 | 整合基础模型 + 双 LiDAR + Gazebo 插件 |
| [urdf/scout_mini.xacro](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/urdf/scout_mini.xacro) | 恢复 | 恢复为原始干净基座模型 |
| [params/slam_toolbox_params.yaml](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/params/slam_toolbox_params.yaml) | 修改 | 优化参数（map_name/mode/minimum_time_interval） |
| [launch/slam.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/launch/slam.launch.py) | 重构 | 只启动 SLAM，不启动 Gazebo/RViz |
| [launch/display.launch.py](file:///home/luoyongkang/scout_nav2_mini/src/external/scout_ros2/scout_description/launch/display.launch.py) | 修复 | 传递 mesh_prefix，指向正确 rviz 配置 |
| [rviz/display.rviz](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/rviz/display.rviz) | 新建 | Fixed Frame=base_link 的 RViz 配置 |
| [CMakeLists.txt](file:///home/luoyongkang/scout_nav2_mini/src/scout_mini_dual_lidar_gazebo/CMakeLists.txt) | 修改 | install 添加 urdf 和 rviz 目录 |

### 生成的地图文件
- `maps/nav2_test_map.pgm` — 地图图像（791×957，0.05 m/pixel）
- `maps/nav2_test_map.yaml` — 地图元数据

### 使用流程

```bash
# 1. 启动仿真
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 2. 启动 SLAM（新终端）
ros2 launch scout_mini_dual_lidar_gazebo slam.launch.py

# 3. 键盘控制建图（新终端）
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 4. 保存地图（地图显示出来后）
mkdir -p maps
ros2 run nav2_map_server map_saver_cli -f maps/nav2_test_map
```

### 测试验证命令

```bash
# 检查 TF 树完整性
ros2 run tf2_tools view_frames

# 检查 /map 话题
ros2 topic echo /map --once

# 检查 Gazebo 默认配置
cat /usr/share/ignition/ignition-gazebo6/server.config

# 检查 Gazebo 内部消息类型
ign topic -i -t /tf
ign topic -i -t /odom
```

### 经验总结

1. **World 中显式声明插件会抑制默认加载**：必须显式声明所有必需插件
2. **Ignition Fortress 使用 `ignition-gazebo-*` 文件名**：`gz-sim-*` 不是有效别名
3. **Gazebo 自动添加模型名前缀到 frame_id**：需静态 TF 桥接
4. **`ros-humble-ros-gz-bridge` 消息类型需匹配 Gazebo 实际类型**：用 `ign topic -i` 确认

### 验证结果
- ✅ 机器人可通过键盘遥控在 Gazebo 中移动
- ✅ 双 LiDAR 数据正常发布（5Hz）
- ✅ SLAM 成功建图，`/map` 话题有数据
- ✅ TF 树完整连接：`map → odom → base_link → sensors`
- ✅ 地图成功保存为 pgm + yaml 文件
- ✅ RViz 中可正常显示 RobotModel

---

## 任务 18 — 导航坐标系解释（重做）

### 目标
确保理解 Nav2 坐标系链，包括 Task 17 调试中发现的 Gazebo 模型名前缀桥接机制。

### 更新的报告
- `reports/navigation_frames.md` — 综合解释（根据实际 TF 树更新）
- `reports/frames_chinese.md` — 中文版（根据实际 TF 树更新）

### 实际 TF 树（Task 17 前缀桥接修复后）

```
map → odom → scout_mini/odom → scout_mini/base_link → base_link → [front_lidar_link, rear_lidar_link]
  SLAM    静态身份变换          diff drive 插件         静态身份变换     robot_state_publisher
```

Gazebo 自动在所有 frame ID 前添加 `scout_mini/` 前缀。两个静态身份 TF 变换桥接命名空间：
- `odom → scout_mini/odom` — 连接 ROS 标准帧到 Gazebo 命名空间里程计帧
- `scout_mini/base_link → base_link` — 连接 Gazebo 命名空间帧到 ROS 标准基座帧

### 各帧详解

#### 1. map 帧（世界帧）
- **原点**：地图原点（世界固定）
- **特点**：全局固定，重定位时可能跳变，由 SLAM/AMCL 维护
- **用途**：全局路径规划、长期导航

#### 2. odom 帧（里程计帧）
- **原点**：机器人启动位置
- **特点**：连续平滑（50 Hz），短期精度高，长期无界漂移
- **用途**：局部路径跟踪、实时运动控制

#### 3. Gazebo 前缀帧（scout_mini/odom, scout_mini/base_link）
- **来源**：Gazebo diff drive 插件输出（带模型名前缀）
- **特点**：零偏移身份变换连接到 ROS 标准帧
- **目的**：连接 Gazebo 的命名空间 TF 发布到 ROS 标准命名

#### 4. base_link 帧（机器人基座帧）
- **位置**：机器人几何中心，离地 0.145m
- **特点**：随机器人移动，所有 URDF 定义的传感器帧的父帧
- **用途**：传感器融合参考、运动控制

#### 5. base_footprint 帧
- **位置**：base_link 在地面上的垂直投影（z = -0.145m）
- **用途**：2D 导航与代价地图参考

#### 6. LiDAR 帧
- **front_lidar_link**：相对 base_link (0.245, 0, 0.14)，朝前，360° 扫描，5 Hz
- **rear_lidar_link**：相对 base_link (-0.245, 0, 0.14)，朝后（偏航 180°），360° 扫描，5 Hz

### 关键区别

#### map vs odom

| 特性 | map | odom |
|------|-----|------|
| **原点** | 世界固定的地图原点 | 机器人启动位置 |
| **连续性** | 不连续（可能跳变） | 连续平滑 |
| **精度** | 长期准确（回环闭合） | 短期精确（无界漂移） |
| **更新频率** | ~2–10 Hz（SLAM） | 50 Hz（diff drive） |
| **发布者** | SLAM Toolbox / AMCL | Gazebo → ros_gz_bridge |
| **用途** | 全局规划 | 局部控制 |

**为什么两者都需要**：`odom` 提供平滑、高频的运动状态。`map → odom` 变换通过调整偏移量来修正漂移，使 SLAM 修正不影响实时控制。

### 验证命令

```bash
ros2 run tf2_tools view_frames          # 查看完整 TF 树
ros2 run tf2_ros tf2_echo map front_lidar_link   # 端到端检查
ros2 run tf2_ros tf2_echo odom base_link         # 里程计链
ros2 run tf2_ros tf2_echo base_link front_lidar_link  # 静态变换
```

### 验证结果
- ✅ 没有断开的坐标系 — 从 map 到所有叶子帧单一的连通 TF 树
- ✅ map vs odom 的区别已清楚解释（离散 vs 连续）
- ✅ 模型名前缀桥接机制已文档化
- ✅ LiDAR 帧位置与 URDF 一致
- ✅ 所有端到端变换可查询

### 提交的文件
- `reports/navigation_frames.md`（根据实际 TF 树更新）
- `reports/frames_chinese.md`（根据实际 TF 树更新）
- `TASK_LOG.md`（已更新）
- `TASK_LOG_CHINESE.md`（已更新）

---
## 任务 19 — 最小化 Nav2 启动

### 目标
在调整导航行为之前，成功启动 Nav2 并使生命周期节点变为活动状态。

### 创建的文件
- `config/nav2_params.yaml` — 最小化 Nav2 参数配置
- `launch/nav2_launch.py` — 最小化 Nav2 启动文件

### 配置的节点

| 节点 | 包 | 用途 |
|------|------|------|
| `map_server` | nav2_map_server | 提供已保存的地图 (.pgm/.yaml) |
| `amcl` | nav2_amcl | 蒙特卡洛定位，使用 /front/scan |
| `planner_server` | nav2_planner | 全局路径（NavFn 规划器） |
| `controller_server` | nav2_controller | 局部路径跟随（DWB 控制器） |
| `recoveries_server` | nav2_behaviors | 旋转/后退/等待恢复 |
| `bt_navigator` | nav2_bt_navigator | 行为树引擎 |
| `waypoint_follower` | nav2_waypoint_follower | 航点执行 |
| `lifecycle_manager` | nav2_lifecycle_manager | 自动激活所有节点 |

### 关键配置详情

**机器人规格：**
- Base frame: `base_link`
- Odometry frame: `odom`
- Global frame: `map`
- LiDAR 扫描话题: `/front/scan`
- 机器人模型: differential（差速驱动）
- 最大速度: 0.5 m/s 线速度，1.0 rad/s 角速度

**代价地图：**
- 分辨率: 0.05 m/pixel（与 SLAM 地图匹配）
- 机器人半径: 0.3 m
- 局部代价地图: 3m × 3m 滚动窗口，5 Hz
- 全局代价地图: 静态地图 + 激光障碍物

**规划器:** NavFn（基本网格 A*）
**控制器:** DWB（动态窗口法）

### 使用方法

```bash
# 终端 1：启动 Gazebo 仿真
ros2 launch scout_mini_dual_lidar_gazebo scout_mini_gazebo.launch.py

# 终端 2：启动 Nav2
ros2 launch scout_mini_dual_lidar_gazebo nav2_launch.py

# 在 RViz 中：用"2D Pose Estimate"设置初始位姿
# 然后用"Nav2 Goal"发送目标点
```

### 验证命令

```bash
ros2 node list                    # 所有 7 个 Nav2 节点 + lifecycle_manager + rviz
ros2 lifecycle nodes              # 检查生命周期状态
ros2 topic list                   # /map, /cmd_vel, /plan, /local_plan 等
```

### 提交的文件
- `config/nav2_params.yaml`（新增）
- `launch/nav2_launch.py`（新增）
- `CMakeLists.txt`（已更新 — 添加 config 目录）
- `TASK_LOG.md`（已更新）
- `TASK_LOG_CHINESE.md`（已更新）
