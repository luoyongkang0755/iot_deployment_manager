from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_learning_examples',
            executable='basic_publisher',
            name='basic_publisher',
            output='screen',
            emulate_tty=True,  # 确保输出立即显示
        ),
        Node(
            package='ros2_learning_examples',
            executable='basic_subscriber',
            name='basic_subscriber',
            output='screen',
            emulate_tty=True,  # 确保输出立即显示
        ),
    ])
