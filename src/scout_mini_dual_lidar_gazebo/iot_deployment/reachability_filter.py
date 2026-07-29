"""候选基座位姿可达性过滤模块。

检查候选位姿到目标的 2D 距离是否在机械臂可达范围内，
以及目标高度是否在机械臂工作高度容差内。
"""

import math
import logging

from geometry_msgs.msg import PoseStamped

from iot_deployment import declare_param
from iot_deployment.candidate_generator import Candidate


class ReachabilityFilter:
    """基于机械臂几何可达性的候选过滤器。

    支持两种构造方式：
      a) ReachabilityFilter(node)：从 ROS node 的 parameter 读取
      b) ReachabilityFilter(node=None, arm_reach_min=..., ...)：直接传参，
         供单元测试使用（不依赖 rclpy 节点上下文）
    """

    DEFAULTS = {
        'arm_reach_min': 0.20,
        'arm_reach_max': 0.60,
        'base_link_z': 0.054,
        'gripper_z_offset': 0.267,
        'height_tolerance': 0.1,
    }

    def __init__(self, node=None, arm_reach_min=None, arm_reach_max=None,
                 base_link_z=None, gripper_z_offset=None, height_tolerance=None):
        if node is not None:
            self.arm_reach_min = declare_param(
                node, 'arm_reach_min', self.DEFAULTS['arm_reach_min'])
            self.arm_reach_max = declare_param(
                node, 'arm_reach_max', self.DEFAULTS['arm_reach_max'])
            self.base_link_z = declare_param(
                node, 'base_link_z', self.DEFAULTS['base_link_z'])
            self.gripper_z_offset = declare_param(
                node, 'gripper_z_offset', self.DEFAULTS['gripper_z_offset'])
            self.height_tolerance = declare_param(
                node, 'height_tolerance', self.DEFAULTS['height_tolerance'])
            self._logger = node.get_logger()
        else:
            self.arm_reach_min = (
                arm_reach_min if arm_reach_min is not None
                else self.DEFAULTS['arm_reach_min'])
            self.arm_reach_max = (
                arm_reach_max if arm_reach_max is not None
                else self.DEFAULTS['arm_reach_max'])
            self.base_link_z = (
                base_link_z if base_link_z is not None
                else self.DEFAULTS['base_link_z'])
            self.gripper_z_offset = (
                gripper_z_offset if gripper_z_offset is not None
                else self.DEFAULTS['gripper_z_offset'])
            self.height_tolerance = (
                height_tolerance if height_tolerance is not None
                else self.DEFAULTS['height_tolerance'])
            self._logger = logging.getLogger('ReachabilityFilter')

        if self.arm_reach_min <= 0.0:
            raise ValueError('arm_reach_min 必须为正')
        if self.arm_reach_max <= self.arm_reach_min:
            raise ValueError('arm_reach_max 必须大于 arm_reach_min')
        if self.height_tolerance <= 0.0:
            raise ValueError('height_tolerance 必须为正')

    def filter(self, candidates: list, target_pose: PoseStamped) -> list:
        """过滤候选位姿列表。

        1. 高度检查：|base_link_z + gripper_z_offset - target_z| < height_tolerance，
           不满足时返回空列表（目标高度超出机械臂工作范围）。
        2. 距离检查：候选到目标的 2D 距离在 [arm_reach_min, arm_reach_max] 内。

        Args:
            candidates: list[Candidate]
            target_pose: map 坐标系下的目标位姿。

        Returns:
            list[Candidate]，通过全部检查的候选。
        """
        tx = target_pose.pose.position.x
        ty = target_pose.pose.position.y
        tz = target_pose.pose.position.z

        # 高度检查：不满足时整个目标不可达，直接返回空
        gripper_z = self.base_link_z + self.gripper_z_offset
        if abs(gripper_z - tz) >= self.height_tolerance:
            self._logger.warning(
                f'目标高度 {tz:.3f} 超出容差 '
                f'(gripper_z={gripper_z:.3f}, tol={self.height_tolerance:.3f})，'
                '全部候选拒绝')
            return []

        # 距离检查
        result = []
        for c in candidates:
            dist = math.hypot(c.x - tx, c.y - ty)
            if self.arm_reach_min <= dist <= self.arm_reach_max:
                result.append(c)
        return result
