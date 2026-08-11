#!/usr/bin/env python3
"""TF 实测校准：发送多个 pick pose，TF 读取 link7 实际位置。
目标：找到 link7 最接近设备位置 (0.115, 0, 0.069) 的 pose。
"""
import sys, time, itertools
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from builtin_interfaces.msg import Duration
from tf2_ros import Buffer, TransformListener

ARM = ['joint1','joint2','joint3','joint4','joint5','joint6']
TARGET = (0.115, 0.0, 0.069)

# 候选 pick poses（限位内，j2 控前后，j3 控上下）
CANDIDATES = []
for j2 in [0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]:
    for j3 in [-0.2, -0.4, -0.6, -0.8, -1.0, -1.2]:
        CANDIDATES.append([0.0, j2, j3, 0.0, 0.9, 0.0])

class ScanNode(Node):
    def __init__(self):
        super().__init__('tf_scan')
        self.cli = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.tf = Buffer()
        TransformListener(self.tf, self)
        self.cli.wait_for_server()
        self.get_logger().info(f'starting scan: {len(CANDIDATES)} candidates')
        self.results = []
        self.idx = 0
        self._next()

    def _next(self):
        if self.idx >= len(CANDIDATES):
            self._report()
            rclpy.shutdown()
            return
        pose = CANDIDATES[self.idx]
        self.get_logger().info(f'[{self.idx+1}/{len(CANDIDATES)}] testing {pose}')
        goal = FollowJointTrajectory.Goal()
        traj = JointTrajectory()
        traj.joint_names = ARM
        pt = JointTrajectoryPoint()
        pt.positions = pose
        pt.time_from_start = Duration(sec=2, nanosec=0)
        traj.points = [pt]
        goal.trajectory = traj
        fut = self.cli.send_goal_async(goal)
        fut.add_done_callback(self._on_goal)

    def _on_goal(self, fut):
        handle = fut.result()
        if not handle.accepted:
            self.get_logger().warn('rejected')
            self.idx += 1
            self._next()
            return
        handle.get_result_async().add_done_callback(self._on_result)

    def _on_result(self, rfut):
        time.sleep(0.3)
        try:
            t = self.tf.lookup_transform('base_link', 'link7', rclpy.time.Time())
            tr = t.transform.translation
            lx, ly, lz = tr.x, tr.y, tr.z
            err = ((lx-TARGET[0])**2 + (ly-TARGET[1])**2 + (lz-TARGET[2])**2)**0.5
            pose = CANDIDATES[self.idx]
            self.results.append((err, list(pose), lx, ly, lz))
            self.get_logger().info(f'  link7=({lx:.4f},{ly:.4f},{lz:.4f}) err={err:.4f}')
        except Exception as e:
            self.get_logger().warn(f'TF error: {e}')
        self.idx += 1
        self._next()

    def _report(self):
        self.results.sort(key=lambda r: r[0])
        print('\n' + '='*70)
        print(f'  TOP 5 (TF 实测)  目标: {TARGET}')
        print('='*70)
        for i, (err, pose, lx, ly, lz) in enumerate(self.results[:5]):
            print(f'  #{i+1} err={err*100:.1f}cm  pose={pose}')
            print(f'      link7=({lx:.4f},{ly:.4f},{lz:.4f})')
            dx,dy,dz = lx-TARGET[0], ly-TARGET[1], lz-TARGET[2]
            print(f'      delta dx={dx:+.4f} dy={dy:+.4f} dz={dz:+.4f}')
        print('='*70)

rclpy.init(args=sys.argv)
rclpy.spin(ScanNode())
