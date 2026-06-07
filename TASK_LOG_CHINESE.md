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
