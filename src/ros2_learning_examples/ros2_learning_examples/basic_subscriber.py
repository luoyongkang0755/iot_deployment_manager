#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# part1 
class MinimalSubscriber(Node):
    def __init__(self):
        super().__init__("basic_subscriber")
        self.subscriber = self.create_subscription(
            String,
            "/student_status",
            self.listener_callback,
            10
        )
        # 删除了无用的 self.subscription 行

    def listener_callback(self, msg):
        self.get_logger().info('I heard: "%s"' % msg.data)

# part2
def main(args=None):
    rclpy.init(args=args)
    node = MinimalSubscriber()
    rclpy.spin(node)
    node.destroy_node()  # 修正拼写：destory -> destroy
    rclpy.shutdown()

# part3
if __name__ == "__main__":
    main()
