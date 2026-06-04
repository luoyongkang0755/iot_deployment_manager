#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String  # 修正1：添加 .msg

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__("basic_publisher")
        self.publisher_ = self.create_publisher(String, "/student_status", 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0  # 修正2：self 不是 slef
    
    def timer_callback(self):
        msg = String()
        msg.data = "Learning ROS 2 topics: %d" % self.i  # 修正：按任务要求改字符串
        self.publisher_.publish(msg)  # 修正3：publisher_.publish 不是 publisher_publish
        self.get_logger().info('Publishing: "%s"' % msg.data)  # 修正4：引号配对
        self.i += 1

def main(args=None):
    rclpy.init(args=args)  # 修正5：args 不是 argss
    node = MinimalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()