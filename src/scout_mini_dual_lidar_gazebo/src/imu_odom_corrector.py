#!/usr/bin/env python3
"""
Odometry pass-through: fixes frame_id from scout_mini/ prefix, optionally
replaces angular velocity with IMU gyro. Pose orientation is kept from
DiffDrive (accurate in simulation) to avoid IMU gyro bias drift.
Subscribes to /odom_raw (raw DiffDrive with scout_mini/ prefix),
publishes corrected /odom (frame_id: odom, child_frame_id: base_link).
TF is handled separately by odom_to_tf node.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
import math


class ImuOdomCorrector(Node):
    def __init__(self):
        super().__init__('imu_odom_corrector')

        self.odom_sub = self.create_subscription(Odometry, '/odom_raw', self.odom_cb, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu', self.imu_cb, 10)
        self.pub = self.create_publisher(Odometry, '/odom', 10)

        self.latest_gyro_z = 0.0

        self.get_logger().info('Odometry pass-through: /odom_raw -> /odom (frame_ids fixed, IMU gyro for angular vel)')

    def imu_cb(self, msg):
        self.latest_gyro_z = msg.angular_velocity.z

    def odom_cb(self, msg):
        out = Odometry()
        out.header = msg.header
        out.header.frame_id = 'odom'
        out.child_frame_id = 'base_link'

        # Keep DiffDrive pose (position + orientation) as-is — accurate in simulation
        out.pose.pose.position = msg.pose.pose.position
        out.pose.pose.orientation = msg.pose.pose.orientation
        out.pose.covariance = list(msg.pose.covariance)

        # Preserve linear velocity, optionally use IMU gyro for angular velocity
        out.twist.twist.linear = msg.twist.twist.linear
        out.twist.twist.angular.x = 0.0
        out.twist.twist.angular.y = 0.0
        out.twist.twist.angular.z = self.latest_gyro_z if abs(self.latest_gyro_z) > 0.001 else msg.twist.twist.angular.z
        out.twist.covariance = list(msg.twist.covariance)

        self.pub.publish(out)


def main():
    rclpy.init()
    node = ImuOdomCorrector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
