#!/usr/bin/env python3
"""
IMU-corrected odometry + TF: replaces DiffDrive rotation with IMU gyro.
Publishes /odom_corrected and TF odom_corrected→base_link.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from geometry_msgs.msg import TransformStamped
import tf2_ros
import math


class ImuOdomCorrector(Node):
    def __init__(self):
        super().__init__('imu_odom_corrector')

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_cb, 10)
        self.imu_sub = self.create_subscription(Imu, '/imu', self.imu_cb, 10)
        self.pub = self.create_publisher(Odometry, '/odom_corrected', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.last_imu_time = None
        self.accumulated_yaw = 0.0
        self.last_odom = None

        self.get_logger().info('IMU-corrected odometry + TF -> odom_corrected')

    def imu_cb(self, msg):
        now = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self.last_imu_time is not None:
            dt = now - self.last_imu_time
            if 0 < dt < 0.1:
                self.accumulated_yaw += msg.angular_velocity.z * dt
        self.last_imu_time = now

    def odom_cb(self, msg):
        yaw = self.accumulated_yaw

        # Publish corrected odometry message
        out = Odometry()
        out.header = msg.header
        out.header.frame_id = 'odom_corrected'
        out.child_frame_id = 'base_link'

        out.pose.pose.position = msg.pose.pose.position
        out.pose.pose.orientation.x = 0.0
        out.pose.pose.orientation.y = 0.0
        out.pose.pose.orientation.z = math.sin(yaw / 2.0)
        out.pose.pose.orientation.w = math.cos(yaw / 2.0)
        out.pose.covariance = list(msg.pose.covariance)

        out.twist.twist.linear = msg.twist.twist.linear
        out.twist.twist.angular = msg.twist.twist.angular
        out.twist.covariance = list(msg.twist.covariance)

        self.pub.publish(out)

        # Publish corrected TF: odom_corrected -> base_link
        tf_msg = TransformStamped()
        tf_msg.header.stamp = msg.header.stamp
        tf_msg.header.frame_id = 'odom_corrected'
        tf_msg.child_frame_id = 'base_link'
        tf_msg.transform.translation.x = out.pose.pose.position.x
        tf_msg.transform.translation.y = out.pose.pose.position.y
        tf_msg.transform.translation.z = out.pose.pose.position.z
        tf_msg.transform.rotation = out.pose.pose.orientation
        self.tf_broadcaster.sendTransform(tf_msg)


def main():
    rclpy.init()
    node = ImuOdomCorrector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
