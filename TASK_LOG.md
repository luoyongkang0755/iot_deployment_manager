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
