#!/usr/bin/env python3
"""IoT deployment 主导航节点。

订阅 /deployment_target (geometry_msgs/PoseStamped, frame_id='map')，
执行候选生成 -> 可达性过滤 -> 占据过滤 -> 评分排序 -> Nav2 逐个尝试导航。
导航成功发布 READY_FOR_MANIPULATION，全部失败发布 DEPLOYMENT_FAILED，
同时发布 /deployment_markers (MarkerArray) 可视化。
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from action_msgs.msg import GoalStatus

from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String, ColorRGBA
from nav2_msgs.action import NavigateToPose
from visualization_msgs.msg import Marker, MarkerArray

from iot_deployment.candidate_generator import CandidateGenerator
from iot_deployment.reachability_filter import ReachabilityFilter
from iot_deployment.occupancy_filter import OccupancyFilter
from iot_deployment.candidate_scorer import CandidateScorer

STATUS_READY = 'READY_FOR_MANIPULATION'
STATUS_FAILED = 'DEPLOYMENT_FAILED'


class DeploymentApproachNode(Node):
    """IoT deployment 导航编排节点。"""

    def __init__(self):
        super().__init__('deployment_approach_node')

        # Pipeline 模块（从本节点参数读取配置）
        self._generator = CandidateGenerator(node=self)
        self._reachability = ReachabilityFilter(node=self)
        self._occupancy = OccupancyFilter(node=self)
        self._scorer = CandidateScorer(node=self)

        # ROS 接口
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._status_pub = self.create_publisher(String, '/deployment_status', 10)
        self._marker_pub = self.create_publisher(
            MarkerArray, '/deployment_markers', 10)
        self.create_subscription(
            PoseStamped, '/deployment_target', self._target_callback, 10)

        # 接近即停：当机器人离目标足够近（或撞到桌子导致导航中止）时，
        # 不再尝试下一个候选，直接视为到达并触发放置。
        self._proximity_threshold = self.declare_parameter(
            'proximity_threshold', 0.8).value  # m
        self._robot_pose = None  # 最新 AMCL 定位位置 (x, y)
        self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose',
            self._amcl_pose_callback, 10)

        # 当前流程状态
        self._target = None          # 当前目标 PoseStamped
        self._valid = []             # 有效候选 list[Candidate]
        self._rejected = []          # 被拒绝候选 list[Candidate]
        self._sorted = []            # 评分排序后 list[(Candidate, float)]
        self._nav_index = 0          # 当前尝试的候选下标
        self._goal_handle = None     # 当前 Nav2 goal handle

        self.get_logger().info('deployment_approach_node 已启动，等待 /deployment_target')

    # ------------------------------------------------------------------
    # 目标回调：取消旧流程，启动新流程
    # ------------------------------------------------------------------
    def _amcl_pose_callback(self, msg: PoseWithCovarianceStamped):
        """跟踪机器人当前位置，用于接近即停判断。"""
        self._robot_pose = (
            msg.pose.pose.position.x, msg.pose.pose.position.y)

    def _target_callback(self, msg: PoseStamped):
        if msg.header.frame_id != 'map':
            self.get_logger().error(
                f'frame_id 必须为 map，收到 "{msg.header.frame_id}"，忽略目标')
            return

        self.get_logger().info(
            f'收到新目标: ({msg.pose.position.x:.2f}, '
            f'{msg.pose.position.y:.2f}, {msg.pose.position.z:.2f})')

        # 取消正在进行的导航
        if self._goal_handle is not None:
            self.get_logger().info('取消正在进行的导航目标')
            self._goal_handle.cancel_goal_async()
            self._goal_handle = None

        self._target = msg
        self._run_pipeline()

    # ------------------------------------------------------------------
    # 候选生成 -> 过滤 -> 评分
    # ------------------------------------------------------------------
    def _run_pipeline(self):
        all_candidates = self._generator.generate(self._target)

        reachable = self._reachability.filter(all_candidates, self._target)
        reach_rejected = [c for c in all_candidates if c not in reachable]

        free = self._occupancy.filter(reachable)
        occ_rejected = [c for c in reachable if c not in free]

        self._valid = free
        self._rejected = reach_rejected + occ_rejected

        self.get_logger().info(
            f'候选统计: 生成 {len(all_candidates)}，'
            f'可达 {len(reachable)}，无碰撞 {len(free)}')

        if not free:
            self.get_logger().warn('无有效候选，发布 DEPLOYMENT_FAILED')
            self._publish_markers()
            self._publish_status(STATUS_FAILED)
            return

        scored = self._scorer.score(free, self._target)
        self._sorted = sorted(scored, key=lambda item: item[1], reverse=True)
        self._nav_index = 0

        self._publish_markers()
        self._try_next_candidate()

    # ------------------------------------------------------------------
    # Nav2 导航尝试
    # ------------------------------------------------------------------
    def _try_next_candidate(self):
        if self._nav_index >= len(self._sorted):
            self.get_logger().warn('全部候选导航失败，发布 DEPLOYMENT_FAILED')
            self._publish_status(STATUS_FAILED)
            return

        candidate, score = self._sorted[self._nav_index]
        self.get_logger().info(
            f'尝试候选 {self._nav_index + 1}/{len(self._sorted)}: '
            f'({candidate.x:.2f}, {candidate.y:.2f}, '
            f'yaw={math.degrees(candidate.yaw):.1f}°), score={score:.3f}')

        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Nav2 action server 不可用')
            self._nav_index += 1
            self._try_next_candidate()
            return

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = candidate.x
        goal.pose.pose.position.y = candidate.y
        goal.pose.pose.position.z = 0.0
        goal.pose.pose.orientation.x = 0.0
        goal.pose.pose.orientation.y = 0.0
        goal.pose.pose.orientation.z = math.sin(candidate.yaw / 2.0)
        goal.pose.pose.orientation.w = math.cos(candidate.yaw / 2.0)

        send_future = self._nav_client.send_goal_async(goal)
        send_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future):
        goal_handle: ClientGoalHandle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('目标被 Nav2 拒绝，尝试下一个候选')
            self._nav_index += 1
            self._try_next_candidate()
            return

        self._goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_callback)

    def _result_callback(self, future):
        self._goal_handle = None
        status = future.result().status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('导航成功，发布 READY_FOR_MANIPULATION')
            self._publish_markers(selected=self._sorted[self._nav_index][0])
            self._publish_status(STATUS_READY)
            return

        if status == GoalStatus.STATUS_CANCELED:
            # 被新目标取消，不再继续旧流程
            self.get_logger().info('导航被取消（收到新目标）')
            return

        # ABORTED 或其他失败状态 -> 检查是否因接近障碍物（桌子）而停
        # 如果机器人当前位置离目标足够近，视为"已到达"并触发放置。
        if self._is_close_to_target():
            self.get_logger().info(
                '导航中止但机器人已接近目标（可能碰到桌子），视为到达')
            self._publish_markers(selected=self._sorted[self._nav_index][0])
            self._publish_status(STATUS_READY)
            return

        self.get_logger().warn(f'导航失败 (status={status})，尝试下一个候选')
        self._nav_index += 1
        self._try_next_candidate()

    def _is_close_to_target(self) -> bool:
        """检查机器人当前位置是否在目标的接近阈值内。"""
        if self._target is None or self._robot_pose is None:
            return False
        dx = self._robot_pose[0] - self._target.pose.position.x
        dy = self._robot_pose[1] - self._target.pose.position.y
        dist = math.hypot(dx, dy)
        self.get_logger().info(f'机器人距目标 {dist:.2f} m (阈值 {self._proximity_threshold:.2f} m)')
        return dist <= self._proximity_threshold

    # ------------------------------------------------------------------
    # 状态与 Marker 发布
    # ------------------------------------------------------------------
    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)

    def _publish_markers(self, selected=None):
        if self._target is None:
            return

        stamp = self.get_clock().now().to_msg()
        markers = []

        # DELETEALL 清空旧 marker
        delete_all = Marker()
        delete_all.header.frame_id = 'map'
        delete_all.header.stamp = stamp
        delete_all.action = Marker.DELETEALL
        markers.append(delete_all)

        # 红球：目标
        markers.append(self._make_target_marker(stamp))

        # 蓝箭头：有效候选（未选中）
        for i, c in enumerate(self._valid):
            if selected is not None and c is selected:
                continue
            markers.append(self._make_arrow_marker(
                100 + i, c, stamp, ColorRGBA(r=0.0, g=0.4, b=1.0, a=0.8)))

        # 灰箭头：被拒绝候选
        for i, c in enumerate(self._rejected):
            markers.append(self._make_arrow_marker(
                200 + i, c, stamp, ColorRGBA(r=0.5, g=0.5, b=0.5, a=0.5)))

        # 绿箭头：选中位姿（导航成功后）
        if selected is not None:
            markers.append(self._make_arrow_marker(
                300, selected, stamp, ColorRGBA(r=0.0, g=1.0, b=0.0, a=1.0),
                scale=(0.4, 0.06, 0.06)))

        self._marker_pub.publish(MarkerArray(markers=markers))

    def _make_target_marker(self, stamp) -> Marker:
        m = Marker()
        m.header.frame_id = 'map'
        m.header.stamp = stamp
        m.ns = 'deployment'
        m.id = 0
        m.type = Marker.SPHERE
        m.action = Marker.ADD
        m.pose = self._target.pose
        m.scale.x = 0.15
        m.scale.y = 0.15
        m.scale.z = 0.15
        m.color = ColorRGBA(r=1.0, g=0.0, b=0.0, a=1.0)
        return m

    @staticmethod
    def _make_arrow_marker(marker_id, candidate, stamp, color,
                           scale=(0.3, 0.04, 0.04)) -> Marker:
        m = Marker()
        m.header.frame_id = 'map'
        m.header.stamp = stamp
        m.ns = 'deployment'
        m.id = marker_id
        m.type = Marker.ARROW
        m.action = Marker.ADD
        m.pose.position.x = candidate.x
        m.pose.position.y = candidate.y
        m.pose.position.z = 0.0
        m.pose.orientation.x = 0.0
        m.pose.orientation.y = 0.0
        m.pose.orientation.z = math.sin(candidate.yaw / 2.0)
        m.pose.orientation.w = math.cos(candidate.yaw / 2.0)
        m.scale.x = scale[0]
        m.scale.y = scale[1]
        m.scale.z = scale[2]
        m.color = color
        return m


def main(args=None):
    rclpy.init(args=args)
    node = DeploymentApproachNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
