#!/usr/bin/env python3
"""Fix LiDAR frame_id: strip scout_mini/ prefix, remap to URDF link names."""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class ScanFrameFixer(Node):
    def __init__(self):
        super().__init__('scan_frame_fixer')

        self.front_pub = self.create_publisher(LaserScan, '/front/scan_fixed', 10)
        self.rear_pub = self.create_publisher(LaserScan, '/rear/scan_fixed', 10)

        self.create_subscription(LaserScan, '/front/scan', self.front_callback, 10)
        self.create_subscription(LaserScan, '/rear/scan', self.rear_callback, 10)

        self.get_logger().info(
            'Scan frame fixer: /front/scan -> /front/scan_fixed (frame_id: front_lidar_link), '
            '/rear/scan -> /rear/scan_fixed (frame_id: rear_lidar_link)')

    def front_callback(self, msg):
        msg.header.frame_id = 'front_lidar_link'
        self.front_pub.publish(msg)

    def rear_callback(self, msg):
        msg.header.frame_id = 'rear_lidar_link'
        self.rear_pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(ScanFrameFixer())
    rclpy.shutdown()


if __name__ == '__main__':
    main()
