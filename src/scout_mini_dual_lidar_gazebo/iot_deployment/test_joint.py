#!/usr/bin/env python3
"""测试单个关节运动。"""
import sys, time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from builtin_interfaces.msg import Duration

class TestNode(Node):
    def __init__(self):
        super().__init__('test_joint')
        self.cli = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.cli.wait_for_server()
        self.get_logger().info('server ready')

        # 测试: home -> joint2=1.5 -> 读 joint_states
        self.get_logger().info('sending home...')
        self._send([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], self._on_home)

    def _send(self, positions, cb):
        g = FollowJointTrajectory.Goal()
        t = JointTrajectory()
        t.joint_names = ['joint1','joint2','joint3','joint4','joint5','joint6']
        p = JointTrajectoryPoint()
        p.positions = positions
        p.time_from_start = Duration(sec=3, nanosec=0)
        t.points = [p]
        g.trajectory = t
        fut = self.cli.send_goal_async(g)
        fut.add_done_callback(lambda f: self._on_goal(f, cb, positions))

    def _on_goal(self, fut, cb, positions):
        h = fut.result()
        if not h.accepted:
            self.get_logger().error(f'goal rejected for {positions}')
            rclpy.shutdown(); return
        self.get_logger().info(f'goal accepted for {positions}')
        h.get_result_async().add_done_callback(lambda rf: cb())

    def _on_home(self):
        time.sleep(0.5)
        self.get_logger().info('sending joint2=1.5...')
        self._send([0.0, 1.5, 0.0, 0.0, 0.0, 0.0], self._on_done)

    def _on_done(self):
        time.sleep(1)
        # 读 joint_states
        from sensor_msgs.msg import JointState
        msg = None
        def cb(m):
            nonlocal msg
            msg = m
        sub = self.create_subscription(JointState, '/joint_states', cb, 10)
        time.sleep(1)
        if msg:
            for n, p in zip(msg.name, msg.position):
                print(f'  {n}: {p:.6f}')
        else:
            print('no joint_states received')
        rclpy.shutdown()

rclpy.init(args=sys.argv)
rclpy.spin(TestNode())
