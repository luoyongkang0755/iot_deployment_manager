#!/usr/bin/env python3
"""
Odometry frame_id fixer: strips scout_mini/ prefix from /odom_raw so that
downstream consumers (robot_localization EKF) receive clean frame_ids.

Publishes /odom with frame_id='odom', child_frame_id='base_link'.
Pose/twist are passed through unchanged — sensor fusion is handled by EKF.

When EKF is not used, this node still provides the corrected /odom that
odom_to_tf broadcasts as TF.
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry


class ImuOdomCorrector(Node):
    def __init__(self):
        super().__init__('imu_odom_corrector')

        self.odom_sub = self.create_subscription(Odometry, '/odom_raw', self.odom_cb, 10)
        self.pub = self.create_publisher(Odometry, '/odom', 10)

        self.get_logger().info('Odometry frame_id fixer: /odom_raw -> /odom (clean frame_ids)')

    def odom_cb(self, msg):
        out = Odometry()
        out.header = msg.header
        out.header.frame_id = 'odom'
        out.child_frame_id = 'base_link'

        # Pass through pose and twist unchanged
        out.pose = msg.pose
        out.twist = msg.twist

        self.pub.publish(out)


def main():
    rclpy.init()
    node = ImuOdomCorrector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
