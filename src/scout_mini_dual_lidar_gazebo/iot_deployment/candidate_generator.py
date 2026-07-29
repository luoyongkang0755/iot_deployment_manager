"""候选基座位姿生成模块。

以 IoT 目标点为中心，在机械臂可达半径环带上均匀生成候选基座位姿，
每个候选 yaw 朝向目标。坐标在 map 坐标系。
"""

import math
from dataclasses import dataclass

from geometry_msgs.msg import PoseStamped

from iot_deployment import declare_param


@dataclass
class Candidate:
    """候选基座位姿（map 坐标系，2D）。"""
    x: float
    y: float
    yaw: float


class CandidateGenerator:
    """在目标周围的可达环带上生成候选基座位姿。

    支持两种构造方式：
      a) CandidateGenerator(node)：从 ROS node 的 parameter 读取
      b) CandidateGenerator(node=None, arm_reach_min=..., ...)：直接传参，
         供单元测试使用（不依赖 rclpy 节点上下文）
    """

    DEFAULTS = {
        'arm_reach_min': 0.20,
        'arm_reach_max': 0.60,
        'candidate_radius_count': 3,
        'candidate_angle_step': 30.0,
    }

    def __init__(self, node=None, arm_reach_min=None, arm_reach_max=None,
                 radius_count=None, angle_step=None):
        if node is not None:
            self.arm_reach_min = declare_param(
                node, 'arm_reach_min', self.DEFAULTS['arm_reach_min'])
            self.arm_reach_max = declare_param(
                node, 'arm_reach_max', self.DEFAULTS['arm_reach_max'])
            self.radius_count = declare_param(
                node, 'candidate_radius_count', self.DEFAULTS['candidate_radius_count'])
            self.angle_step = declare_param(
                node, 'candidate_angle_step', self.DEFAULTS['candidate_angle_step'])
        else:
            self.arm_reach_min = (
                arm_reach_min if arm_reach_min is not None
                else self.DEFAULTS['arm_reach_min'])
            self.arm_reach_max = (
                arm_reach_max if arm_reach_max is not None
                else self.DEFAULTS['arm_reach_max'])
            self.radius_count = (
                radius_count if radius_count is not None
                else self.DEFAULTS['candidate_radius_count'])
            self.angle_step = (
                angle_step if angle_step is not None
                else self.DEFAULTS['candidate_angle_step'])

        if self.arm_reach_min <= 0.0:
            raise ValueError('arm_reach_min 必须为正')
        if self.arm_reach_max <= self.arm_reach_min:
            raise ValueError('arm_reach_max 必须大于 arm_reach_min')
        if self.radius_count < 1:
            raise ValueError('candidate_radius_count 必须 >= 1')
        if self.angle_step <= 0.0 or self.angle_step > 360.0:
            raise ValueError('candidate_angle_step 必须在 (0, 360] 内')

    def generate(self, target_pose: PoseStamped) -> list:
        """生成候选基座位姿列表。

        在 [arm_reach_min, arm_reach_max] 之间均匀取 radius_count 圈半径，
        每圈按 angle_step（度）均匀分布候选点，yaw 朝向目标。

        Args:
            target_pose: map 坐标系下的目标位姿。

        Returns:
            list[Candidate]，总数 = radius_count * (360 / angle_step)。
        """
        tx = target_pose.pose.position.x
        ty = target_pose.pose.position.y

        per_ring = int(round(360.0 / self.angle_step))

        # 均匀半径：radius_count==1 时取最大半径，否则线性插值
        if self.radius_count == 1:
            radii = [self.arm_reach_max]
        else:
            step = (self.arm_reach_max - self.arm_reach_min) / (self.radius_count - 1)
            radii = [self.arm_reach_min + i * step for i in range(self.radius_count)]

        candidates = []
        for radius in radii:
            for k in range(per_ring):
                angle = math.radians(k * self.angle_step)
                x = tx + radius * math.cos(angle)
                y = ty + radius * math.sin(angle)
                yaw = math.atan2(ty - y, tx - x)
                candidates.append(Candidate(x=x, y=y, yaw=yaw))
        return candidates
