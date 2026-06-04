# Docker 基础与 ROS 2 Humble 最小环境报告

## Docker 是什么？
Docker 是一个开源的容器化平台，它允许开发者将应用程序及其依赖项打包到一个轻量级、可移植的容器中。容器与宿主机共享操作系统内核，但通过命名空间和控制组（cgroups）实现进程隔离和资源限制。

## 为什么使用 Docker？
- **可重现性**：无论在哪种 Linux 发行版上，Docker 容器都能提供完全相同的运行环境，避免“在我机器上能跑”的问题。
- **隔离性**：容器内操作不会影响宿主机，便于测试不同的软件版本或配置。
- **简易分发**：通过 Dockerfile 或镜像仓库，团队可以快速分享开箱即用的开发环境。
- **节省资源**：相比虚拟机，容器无需模拟完整操作系统，启动快且占用内存小。

## Dockerfile 安装/配置了什么？
本 Dockerfile 基于 `ros:humble-ros-base`（包含 ROS 2 Humble 核心包、Ubuntu 22.04 基础系统），额外执行了以下操作：

1. **安装工具**  
   - `python3-colcon-common-extensions`：提供 `colcon` 命令行工具，用于构建 ROS 2 工作空间。  
   - `build-essential`：提供 `gcc`、`g++`、`make` 等编译工具链。

2. **环境设置**  
   - 在 `~/.bashrc` 中添加 `source /opt/ros/humble/setup.bash`，使得每次进入容器时 ROS 2 环境自动生效。

3. **创建工作空间与示例包**  
   - 建立 `/ros2_ws/src` 目录作为 ROS 2 工作空间的源码空间。  
   - 使用 `ros2 pkg create` 生成一个名为 `my_package` 的 python 包（`ament_python` 类型）。该包包含标准的 `package.xml` ，可被 `colcon build` 正常构建。

4. **工作目录设置**  
   - 将镜像的默认工作目录设为 `/ros2_ws`，用户进入容器后可直接运行 `colcon build`。

## 验证方法
1. 执行 `bash docker/run_container.sh` 启动容器。  
2. 在容器内执行 `colcon build`。  
3. 观察输出，看到类似 “Summary: 1 package finished” 的成功信息（参见附件 `media/LOG/task7.log`）。  
4. 构建产物位于 `/ros2_ws/build`、`/ros2_ws/install` 等目录中。



