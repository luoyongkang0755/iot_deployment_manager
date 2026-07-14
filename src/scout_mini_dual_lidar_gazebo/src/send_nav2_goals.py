#!/usr/bin/env python3
"""
Task 22 — Send Three Nav2 Goal Points

Sends three navigation goals sequentially via the Nav2 NavigateToPose action server.
Logs the result (success/failure), elapsed time, and remarks for each goal.

Usage:
    ros2 run scout_mini_dual_lidar_gazebo send_nav2_goals.py

Modify the GOALS list below to change target poses.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
import time


# ============================================================
# Configurable goals: (x, y, yaw) in map frame
# Modify these coordinates to test different target positions.
# ============================================================
GOALS = [
    (2.0, 0.0, 0.0),     # Goal 1: Forward 2m along +X
    (-2.0, 2.0, 0.0),    # Goal 2: Navigate to quadrant II
    (2.0, -2.0, 0.0),    # Goal 3: Navigate to quadrant IV
]

INITIAL_POSE = (0.0, 0.0, 0.0)  # (x, y, yaw) — initial pose estimate


class ThreeGoalTester(Node):
    """Node that sends three Nav2 goals and records results."""

    def __init__(self):
        super().__init__('three_goal_tester')

        # Nav2 action client
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Initial pose publisher (for setting AMCL initial estimate)
        self._initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped, 'initialpose', 10)

        self._goal_index = 0
        self._goal_start_time = None
        self._results = []

    def set_initial_pose(self):
        """Publish the initial pose estimate for AMCL localization."""
        x, y, yaw = INITIAL_POSE
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.z = 0.0
        msg.pose.pose.orientation.w = 1.0
        # Set covariance (default uncertainty)
        msg.pose.covariance[0] = 0.25
        msg.pose.covariance[7] = 0.25
        msg.pose.covariance[35] = 0.068
        # Publish several times to ensure AMCL receives it
        for _ in range(5):
            self._initial_pose_pub.publish(msg)
            time.sleep(0.1)
        self.get_logger().info(f'Initial pose set: ({x:.1f}, {y:.1f}, {yaw:.1f})')

    def send_next_goal(self):
        """Send the next goal in the GOALS list."""
        if self._goal_index >= len(GOALS):
            self.print_summary()
            self.get_logger().info('All goals completed. Shutting down.')
            rclpy.shutdown()
            return

        x, y, yaw = GOALS[self._goal_index]
        self.get_logger().info(
            f'\n{"="*60}\n'
            f'  Sending Goal {self._goal_index + 1}/{len(GOALS)}: '
            f'position=({x:.1f}, {y:.1f}), yaw={yaw:.1f}\n'
            f'{"="*60}'
        )

        # Wait for action server
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('NavigateToPose action server not available!')
            self._results.append(('失败', '—', '—', 'Action server not available'))
            self._goal_index += 1
            self.send_next_goal()
            return

        # Build goal message
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0

        self._goal_start_time = self.get_clock().now()
        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Handle goal acceptance/rejection."""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(
                f'Goal {self._goal_index + 1} rejected by Nav2 server!')
            self._results.append(('失败', '—', '—', 'Goal rejected'))
            self._goal_index += 1
            self.send_next_goal()
            return

        self.get_logger().info(
            f'Goal {self._goal_index + 1} accepted. Navigating...')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        """Process navigation feedback."""
        feedback = feedback_msg.feedback
        dist_remaining = feedback.distance_remaining
        self.get_logger().info(
            f'  Distance remaining: {dist_remaining:.2f} m',
            throttle_duration_sec=2.0)

    def result_callback(self, future):
        """Process the final result of a navigation goal."""
        elapsed = self.get_clock().now() - self._goal_start_time
        elapsed_sec = elapsed.nanoseconds * 1e-9
        status = future.result().status
        result = future.result().result

        if status == 4:  # SUCCEEDED
            outcome = '成功'
            remark = '正常到达目标点'
        elif status == 5:  # ABORTED
            outcome = '失败'
            remark = '目标被中止 — 可能由于障碍物或超时'
        elif status == 6:  # CANCELED
            outcome = '失败'
            remark = '目标被取消'
        else:
            outcome = '失败'
            remark = f'未知状态码: {status}'

        self.get_logger().info(
            f'  Goal {self._goal_index + 1} result: {outcome} '
            f'(status={status}, elapsed={elapsed_sec:.1f}s)')
        self.get_logger().info(f'  Remark: {remark}')

        # Record result
        x, y, yaw = GOALS[self._goal_index]
        collision = '—'  # Cannot auto-detect; user should verify visually
        self._results.append((
            f'({INITIAL_POSE[0]:.1f}, {INITIAL_POSE[1]:.1f}, {INITIAL_POSE[2]:.1f})',
            f'({x:.1f}, {y:.1f}, {yaw:.1f})',
            outcome,
            f'{elapsed_sec:.1f}s',
            collision,
            remark
        ))

        # Wait between goals for stabilization
        self._goal_index += 1
        self.get_logger().info('Waiting 3s before next goal...')
        time.sleep(3.0)
        self.send_next_goal()

    def print_summary(self):
        """Print a formatted summary table of all results."""
        self.get_logger().info(
            f'\n{"="*80}\n'
            f'  THREE-GOAL NAVIGATION TEST — RESULTS SUMMARY\n'
            f'{"="*80}'
        )
        self.get_logger().info(
            f'  {"测试":<6} {"初始位姿":<22} {"目标位姿":<22} '
            f'{"结果":<6} {"时间":<10} {"碰撞？":<6} {"备注"}'
        )
        self.get_logger().info(f'  {"-"*78}')
        for i, (init, goal, outcome, t, collision, note) in enumerate(self._results):
            self.get_logger().info(
                f'  {i+1:<6} {init:<22} {goal:<22} '
                f'{outcome:<6} {t:<10} {collision:<6} {note}'
            )
        self.get_logger().info(f'{"="*80}\n')


def main():
    rclpy.init()
    tester = ThreeGoalTester()

    # Set initial pose first, then send goals after a short delay
    tester.set_initial_pose()
    tester.get_logger().info(
        'Waiting 5s for AMCL to converge on initial pose...')
    time.sleep(5.0)
    tester.send_next_goal()

    rclpy.spin(tester)


if __name__ == '__main__':
    main()
