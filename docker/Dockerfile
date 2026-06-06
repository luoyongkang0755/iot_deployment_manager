FROM ros:humble-ros-base

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
SHELL ["/bin/bash", "-c"]

# 基础工具与 colcon 安装
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-joint-state-publisher \
        ros-humble-joint-state-publisher-gui \
        ros-humble-xacro \
	build-essential \
	cmake \
	git \
	python3-pip \
	python3-colcon-common-extensions \
	python3-rosdep \
	ros-humble-rviz2 \
	ros-humble-gazebo-ros-pkgs \
	ros-humble-xacro \
	ros-humble-tf2-tools \
	curl \
	wget \
	lsb-release \
	gnupg2 \
	libasio-dev \
	&& rm -rf /var/lib/apt/lists/*

# 初始化 rosdep（若未初始化则执行 init；保留 update 的真实错误以便调试）
RUN if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then rosdep init; fi && rosdep update

# 创建工作区，复制源码并安装包依赖后构建
WORKDIR /ws

# 将仓库中的 src 目录复制进镜像（构建上下文应为仓库根目录）
COPY src ./src

# 可选：workspace 中可能包含 requirements.txt
# 显式使用 python -m pip 升级 pip/setuptools/wheel，确保构建时支持可编辑安装
RUN python3 -m pip install --upgrade pip "setuptools==67.8.0" wheel
RUN if [ -f src/requirements.txt ]; then python3 -m pip install -r src/requirements.txt || true; fi

# 安装系统依赖并构建工作区
RUN /bin/bash -lc "source /opt/ros/humble/setup.bash && rosdep install -y --from-paths src --ignore-src --rosdistro humble -r || true"
RUN /bin/bash -lc "source /opt/ros/humble/setup.bash && colcon build --symlink-install"

# 入口脚本（将会 source ROS 与工作区环境）
COPY docker/ros_entrypoint.sh /ros_entrypoint.sh
RUN chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
