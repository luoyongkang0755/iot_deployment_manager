cmake_minimum_required(VERSION 3.8)
project(scout_mini_dual_lidar_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(scout_description REQUIRED)
find_package(ros_gz_sim REQUIRED)
find_package(robot_state_publisher REQUIRED)

install(DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}/
)

ament_package()
