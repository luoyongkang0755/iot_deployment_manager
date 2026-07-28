cmake_minimum_required(VERSION 3.8)
project(scout_mini_dual_lidar_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(scout_description REQUIRED)
find_package(ros_gz_sim REQUIRED)
find_package(robot_state_publisher REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(tf2_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

install(DIRECTORY launch worlds params config urdf rviz maps
  DESTINATION share/${PROJECT_NAME}/
)

# Python 模块（DIRECTORY 安装是拷贝，修改 iot_deployment/ 后需重新 colcon build）
install(DIRECTORY iot_deployment
  DESTINATION lib/python3.10/site-packages
)

install(PROGRAMS
  src/tf_static_relay.py
  src/tf_to_odom.py
  src/odom_to_tf.py
  src/laser_merger.py
  src/auto_path_driver.py
  src/imu_odom_corrector.py
  src/scan_frame_fixer.py
  src/send_nav2_goals.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
