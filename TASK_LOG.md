# 任务日志

## [2026-06-03] 仓库初始化
- 创建仓库 `scout_mini_nav2`
- 初始化 Git 仓库并添加如下文件：
  - `README.md`：项目目标说明
  - `TASK_LOG.md`：本日志文件
  - `.gitignore`：忽略临时/编译文件
- 建立标准 ROS2 工作空间目录结构：
  `src/`, `maps/`, `worlds/`, `config/`, `launch/`, `bags/`, `media/screenshots/`, `reports/`, `docker/`
- 完成首次提交：`Initialize Scout Mini dual LiDAR Nav2 assignment repository`
- 关联远程仓库并推送至 `master` 分支

## [2026-06-04] 任务2：基本 Linux 终端命令

### 做了什么
- 在项目根目录依次执行了 `pwd`, `ls`, `mkdir test_folder`, `touch test_folder/test.txt`, `echo "ROS learning task" > test_folder/test.txt`, `cat test_folder/test.txt`, `rm -r test_folder`。
- 将每个命令的输出和解释整理成详细报告，保存为 `reports/linux_basic_commands.md`。

### 命令列表
1. `pwd` – 显示当前目录
2. `ls` – 列出目录内容
3. `mkdir test_folder` – 创建测试文件夹
4. `touch test_folder/test.txt` – 创建空文件
5. `echo "..." > test_folder/test.txt` – 写入内容
6. `cat test_folder/test.txt` – 读取文件内容
7. `rm -r test_folder` – 递归删除测试文件夹

### 哪些有效/失败
- 所有命令均执行成功，无报错。
- `rm -r` 需谨慎使用，本次仅删除临时测试目录，未影响项目文件。

### 学到什么
- 理解了 `pwd` 显示绝对路径、`ls` 可加 `-la` 查看隐藏文件。
- 学会了用 `>` 重定向快速生成配置文件。
- 记住了 `rm -r` 会永久删除，操作前务必确认路径。

# 任务 3 — 创建基本 ROS 2 工作空间包

## 目标
理解 ROS 2 工作空间结构，并创建第一个功能包。

## 创建的包
- **包名**：`ros2_learning_examples`
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

# 编译工作空间
colcon build

# 加载环境设置
source install/setup.bash

# 验证包是否已安装
ros2 pkg list | grep ros2_learning_examples

## [2025-06-04] Task 4 – ROS 2 Publisher and Subscriber

### What was done
- Created a Python publisher node (`basic_publisher.py`) that publishes `"Learning ROS 2 topics"` to the topic `/student_status` at 1 Hz.
- Created a Python subscriber node (`basic_subscriber.py`) that listens to `/student_status` and prints received messages.
- Verified communication using ROS 2 command-line tools.

### Commands used
```bash
# Build the workspace (if needed)
cd ~/scout_mini_dual_lidar_nav2
colcon build --packages-select ros2_learning_examples
source install/setup.bash

# Run publisher (terminal 1)
ros2 run ros2_learning_examples basic_publisher

# Run subscriber (terminal 2)
ros2 run ros2_learning_examples basic_subscriber

# Topic inspection (terminal 3)
ros2 topic list
ros2 topic echo /student_status
ros2 topic hz /student_status

## 任务5 — ROS 2 启动文件

**目标**：用一个启动文件同时启动发布者和订阅者节点。

**完成内容**：
- 创建文件：`src/ros2_learning_examples/launch/basic_pubsub.launch.py`
- 编写 Python 启动脚本，使用 `LaunchDescription` 和 `Node` 动作同时启动两个节点。

**启动文件作用解释**：
ROS 2 启动文件（launch file）用于一次性启动多个节点，并可配置节点参数、命名空间、重映射等。其主要优点包括：
- **简化启动流程**：避免在多个终端中分别执行 `ros2 run`，一个命令即可启动整个系统。
- **集中管理**：可以统一设置节点的输出、环境变量、参数文件等。
- **提高可复现性**：将节点组合以代码形式固化，便于团队协作和实验复现。
- **支持条件启动与事件**：可以根据条件（如检测到设备）动态决定是否启动某节点。

本启动文件具体实现了：
- 同时启动发布者节点（`talker_node`）和订阅者节点（`listener_node`）。
- 设置 `output='screen'` 使节点打印信息直接显示在终端。
- 通过 `emulate_tty=True` 确保消息实时刷新。

**验证步骤**：
1. 在终端执行命令：`ros2 launch ros2_learning_examples basic_pubsub.launch.py`
2. 观察到两个节点同时启动，并输出通信日志。
3. 打开另一个终端，使用 `ros2 node list` 可看到 `/talker_node` 和 `/listener_node`。
4. 使用 `ros2 topic echo /chatter` 确认话题消息正常传输。

**证据**：启动输出截图（`task5`）显示发布者发布消息，订阅者成功接收。

# 任务6 — TF 基础报告

## 1. TF 坐标是什么？

TF（Transform）是 ROS 2 中用于管理不同坐标系之间相对位置和姿态关系的核心工具。它维护着一棵 **TF 树（TF Tree）**，树中的每个节点代表一个坐标系，每个有向边代表从一个坐标系到另一个坐标系的变换（平移 + 旋转）。

通过 TF，系统中任意一个坐标系下的数据（如激光雷达点云、相机图像）都可以实时转换到另一个坐标系下。例如，激光雷达检测到的障碍物坐标可以自动转换到机器人的中心坐标系，供导航算法使用。

## 2. 机器人中的三个重要坐标系

- **`base_link`**  
  固定在机器人本体上的坐标系，通常原点位于机器人的几何中心或旋转中心。它随机器人运动而运动，是描述车上所有传感器、关节等部件安装位置的参考系。

- **`odom`（里程计坐标系）**  
  基于机器人内部传感器（如轮式编码器、IMU）推算出的**局部坐标系**。该坐标系会随时间累积漂移，但短期相对精度较高。`odom` 与 `base_link` 之间的变换直接反映了里程计给出的机器人运动增量。

- **`map`（地图坐标系）**  
  基于外部传感器（如激光雷达、GPS）构建的**全局固定坐标系**，不存在漂移问题。它是导航任务中机器人最终期望使用的绝对参考系。

**三者之间的典型关系**：  
`map → odom → base_link`  
- `map → odom`：修正里程计的长期漂移（由 SLAM 或定位模块提供）。  
- `odom → base_link`：由里程计实时推算，提供平滑的短时运动估计。

## 3. 为什么 LiDAR 需要连接到 `base_link`？

激光雷达（`front_lidar_link`）是一个物理传感器，它固定在机器人上的某个位置。其测量数据（例如 `[x, y]` 障碍物坐标）是相对于它自身的坐标系（原点在 LiDAR 中心）给出的。然而，机器人的决策系统需要知道这些障碍物相对于机器人本体的位置，才能正确进行避障和路径规划。

因此，必须通过 TF 建立一个静态变换（`static_transform_publisher`），明确告知系统：**`base_link` 与 `front_lidar_link` 之间的固定空间关系**。这样，`tf2_ros` 就能够自动地将 LiDAR 数据转换到 `base_link` 下，实现了传感器数据与机器人本体的统一。


