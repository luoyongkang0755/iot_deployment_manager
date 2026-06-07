FROM ros:humble-ros-base

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
SHELL ["/bin/bash", "-c"]

# 使用清华大学镜像源加速 apt
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list && \
    sed -i 's@//.*security.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list

# 基础工具与 colcon 安装
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-joint-state-publisher \
        ros-humble-joint-state-publisher-gui \
	build-essential \
	cmake \
	nano \
	git \
	python3-pip \
	python3-colcon-common-extensions \
	python3-rosdep \
	ros-humble-rviz2 \
	ros-humble-gazebo-ros-pkgs \
	ros-humble-ros-gz-sim \
	ros-humble-xacro \
	ros-humble-tf2-tools \
	curl \
	wget \
	lsb-release \
	gnupg2 \
	libasio-dev \
	&& rm -rf /var/lib/apt/lists/*

# 配置 rosdep 使用清华大学镜像源（解决 raw.githubusercontent.com 超时问题）
RUN mkdir -p /etc/ros/rosdep/sources.list.d && \
    echo "yaml https://mirrors.tuna.tsinghua.edu.cn/rosdistro/rosdep/base.yaml" > /etc/ros/rosdep/sources.list.d/20-default.list && \
    echo "yaml https://mirrors.tuna.tsinghua.edu.cn/rosdistro/rosdep/python.yaml" >> /etc/ros/rosdep/sources.list.d/20-default.list && \
    echo "yaml https://mirrors.tuna.tsinghua.edu.cn/rosdistro/rosdep/osx-homebrew.yaml osx" >> /etc/ros/rosdep/sources.list.d/20-default.list

# 更新 rosdep（带重试机制）
ENV ROSDEP_SOURCE_TIMEOUT=300
RUN for i in 1 2 3 4 5; do \
        echo "Attempt $i: rosdep update..." && \
        rosdep update && break || (echo "Failed, retrying in 10s..." && sleep 10); \
    done

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
