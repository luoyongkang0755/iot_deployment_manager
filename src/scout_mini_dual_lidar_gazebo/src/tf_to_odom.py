#!/usr/bin/env python3
"""
TF to Odometry converter for Scout Mini.
Subscribes to /model/scout_mini/tf and republishes as /odom (nav_msgs/Odometry).
"""

import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import Quaternion
from nav_msgs.msg import Odometry
import math


class TfToOdom(Node):
    def __init__(self):
        super().__init__('tf_to_odom')

        # Publishers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # Subscribers - Gazebo publishes TFMessage containing Pose_V
        self.tf_sub = self.create_subscription(
            TFMessage,
            '/model/scout_mini/tf',
            self.tf_callback,
            10)

        # State
        self.last_x = 0.0
        self.last_y = 0.0
        self.last_theta = 0.0
        self.last_stamp = None
        self.initialized = False

        self.get_logger().info('TF to Odometry converter initialized')

    def tf_callback(self, msg: TFMessage):
        if not msg.transforms:
            return

        # Get the first transform
        tf = msg.transforms[0]
        # Extract position
        x = tf.transform.translation.x
        y = tf.transform.translation.y

        # Extract orientation (quaternion to euler)
        q = tf.transform.rotation
        theta = self.quaternion_to_yaw(q)

        # Extract timestamp
        tf_header = tf.header
        if hasattr(tf_header, 'stamp'):
            current_stamp = tf_header.stamp
        else:
            current_stamp = self.get_clock().now().to_msg()

        # Calculate velocity if initialized
        if self.initialized:
            # Compute actual dt from timestamp difference
            if self.last_stamp is not None:
                dt_ns = (current_stamp.sec - self.last_stamp.sec) * 1e9 + \
                        (current_stamp.nanosec - self.last_stamp.nanosec)
                dt = dt_ns / 1e9
            else:
                dt = 0.02  # fallback for first frame

            # Clamp dt to avoid divide-by-zero or huge velocity spikes
            dt = max(dt, 0.001)
            dt = min(dt, 0.5)

            vx = (x - self.last_x) / dt
            vy = (y - self.last_y) / dt
            vtheta = (theta - self.last_theta) / dt

            # Handle angle wrap-around
            if vtheta > math.pi:
                vtheta -= 2 * math.pi
            elif vtheta < -math.pi:
                vtheta += 2 * math.pi

            # Publish odometry
            odom = Odometry()
            odom.header.stamp = current_stamp
            odom.header.frame_id = 'odom'
            odom.child_frame_id = 'base_link'

            odom.pose.pose.position.x = x
            odom.pose.pose.position.y = y
            odom.pose.pose.position.z = 0.0
            odom.pose.pose.orientation = q

            odom.twist.twist.linear.x = vx
            odom.twist.twist.linear.y = vy
            odom.twist.twist.linear.z = 0.0
            odom.twist.twist.angular.x = 0.0
            odom.twist.twist.angular.y = 0.0
            odom.twist.twist.angular.z = vtheta

            self.odom_pub.publish(odom)
        else:
            self.initialized = True

        self.last_x = x
        self.last_y = y
        self.last_theta = theta
        self.last_stamp = current_stamp

    def quaternion_to_yaw(self, q: Quaternion) -> float:
        """Convert quaternion to yaw angle."""
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)


def main(args=None):
    rclpy.init(args=args)
    node = TfToOdom()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()