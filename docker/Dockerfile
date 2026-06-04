FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y \
        python3-colcon-common-extensions \
        build-essential \
        ros-humble-rviz2 \
        ros-humble-gazebo-ros-pkgs \
        ros-humble-gazebo-ros2-control \
        mesa-utils \
    && \
    
    rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

RUN mkdir -p /ros2_ws/src
WORKDIR /ros2_ws/src

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && \
                  ros2 pkg create my_package --build-type ament_python"

WORKDIR /ros2_ws

CMD ["/bin/bash"]


