import os
import launch
import launch_ros
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch.substitutions import Command, EnvironmentVariable
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_scout_description = get_package_share_directory('scout_description')
    pkg_scout_gazebo = get_package_share_directory('scout_mini_dual_lidar_gazebo')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Launch configuration variables
    world = LaunchConfiguration('world')
    model = LaunchConfiguration('model')
    use_sim_time = LaunchConfiguration('use_sim_time')
    verbose = LaunchConfiguration('verbose')

    # Declare launch arguments
    declare_world_cmd = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_scout_gazebo, 'worlds', 'simple_test_world.world'),
        description='Full path to the world model file to load')

    declare_model_cmd = DeclareLaunchArgument(
        'model',
        default_value=os.path.join(pkg_scout_description, 'urdf', 'scout_mini.xacro'),
        description='Full path to the robot URDF/XACRO file')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_verbose_cmd = DeclareLaunchArgument(
        'verbose',
        default_value='false',
        description='Enable verbose output')

    # Get URDF via xacro with mesh_prefix parameter
    # Use file:// URI for Gazebo compatibility
    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        model,
        ' mesh_prefix:=file://' + pkg_scout_description,
    ])

    robot_description = {'robot_description': robot_description_content}

    # Robot State Publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': use_sim_time}])

    # Gazebo launch using Ignition Gazebo (ros_gz_sim)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={
            'gz_args': ['-v 4 ', world] if verbose else world,
        }.items(),
    )

    # Spawn robot in Gazebo using ros_gz_sim
    # z = |wheel_vertical_offset| + wheel_radius = 0.060 + 0.145 = 0.205m for scout_mini
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'scout_mini',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.205',  # wheel_vertical_offset(0.060) + wheel_radius(0.145)
        ],
        output='screen')

    # ROS-Gazebo Bridge for /cmd_vel (ROS2 -> Gazebo)
    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='cmd_vel_bridge',
        output='screen',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist'
        ])

    # ROS-Gazebo Bridge for /tf (Gazebo -> ROS2)
    tf_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='tf_bridge',
        output='screen',
        arguments=[
            '/model/scout_mini/tf@tf2_msgs/msg/TFMessage@ignition.msgs.Pose_V'
        ])

    # TF to Odometry converter - provides /odom from Gazebo TF
    tf_to_odom = Node(
        package='scout_mini_dual_lidar_gazebo',
        executable='tf_to_odom.py',
        name='tf_to_odom',
        output='screen')

    # Set environment variables for Gazebo resource paths
    # Need to include scout_description's meshes directory for DAE files
    gz_resource_path = pkg_scout_description + '/meshes:' + pkg_scout_gazebo + '/worlds'
    set_env_vars = [
        SetEnvironmentVariable(
            name='GZ_SIM_RESOURCE_PATH',
            value=gz_resource_path
        ),
        SetEnvironmentVariable(
            name='IGN_GAZEBO_RESOURCE_PATH',
            value=gz_resource_path
        ),
    ]

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_world_cmd)
    ld.add_action(declare_model_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_verbose_cmd)

    # Add environment variables
    for env_var in set_env_vars:
        ld.add_action(env_var)

    # Add the nodes to the launch description
    ld.add_action(gazebo)
    ld.add_action(node_robot_state_publisher)
    ld.add_action(spawn_entity)
    ld.add_action(cmd_vel_bridge)
    ld.add_action(tf_bridge)
    ld.add_action(tf_to_odom)

    return ld
