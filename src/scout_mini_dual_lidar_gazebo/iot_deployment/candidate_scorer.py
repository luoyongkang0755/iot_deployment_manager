"""候选基座位姿评分模块。

对每个候选位姿计算距离分和朝向分，加权求和得到总分，
并提供选出最优候选的接口。
"""

import math

from geometry_msgs.msg import PoseStamped

from iot_deployment.candidate_generator import Candidate


class CandidateScorer:
    """候选基座位姿评分器。

    支持两种构造方式：
      a) CandidateScorer(node)：从 ROS node 的 parameter 读取
      b) CandidateScorer(node=None, arm_reach_max=..., ...)：直接传参，
         供单元测试使用（不依赖 rclpy 节点上下文）
    """

    DEFAULTS = {
        'arm_reach_max': 0.60,
        'ideal_reach_ratio': 0.7,
        'reach_sigma': 0.1,
        'score_distance_weight': 0.6,
        'score_heading_weight': 0.4,
    }

    def __init__(self, node=None, arm_reach_max=None, ideal_reach_ratio=None,
                 reach_sigma=None, score_distance_weight=None,
                 score_heading_weight=None):
        if node is not None:
            self.arm_reach_max = node.declare_parameter(
                'arm_reach_max', self.DEFAULTS['arm_reach_max']).value
            self.ideal_reach_ratio = node.declare_parameter(
                'ideal_reach_ratio', self.DEFAULTS['ideal_reach_ratio']).value
            self.reach_sigma = node.declare_parameter(
                'reach_sigma', self.DEFAULTS['reach_sigma']).value
            self.score_distance_weight = node.declare_parameter(
                'score_distance_weight',
                self.DEFAULTS['score_distance_weight']).value
            self.score_heading_weight = node.declare_parameter(
                'score_heading_weight',
                self.DEFAULTS['score_heading_weight']).value
        else:
            self.arm_reach_max = (
                arm_reach_max if arm_reach_max is not None
                else self.DEFAULTS['arm_reach_max'])
            self.ideal_reach_ratio = (
                ideal_reach_ratio if ideal_reach_ratio is not None
                else self.DEFAULTS['ideal_reach_ratio'])
            self.reach_sigma = (
                reach_sigma if reach_sigma is not None
                else self.DEFAULTS['reach_sigma'])
            self.score_distance_weight = (
                score_distance_weight if score_distance_weight is not None
                else self.DEFAULTS['score_distance_weight'])
            self.score_heading_weight = (
                score_heading_weight if score_heading_weight is not None
                else self.DEFAULTS['score_heading_weight'])

        if self.reach_sigma <= 0.0:
            raise ValueError('reach_sigma 必须为正')
        if not (0.0 < self.ideal_reach_ratio < 1.0):
            raise ValueError('ideal_reach_ratio 必须在 (0, 1) 内')

    def score(self, candidates: list,
              target_pose: PoseStamped) -> list:
        """对每个候选计算加权总分。

        距离分：高斯分布，理想距离 = arm_reach_max * ideal_reach_ratio，
               标准差 reach_sigma。
        朝向分：(1 + cos(diff)) / 2，归一化到 [0, 1]。
        总分 = score_distance_weight * 距离分 + score_heading_weight * 朝向分。

        Args:
            candidates: list[Candidate]
            target_pose: map 坐标系下的目标位姿。

        Returns:
            list[(Candidate, float)]，与输入等长的 (候选, 总分) 列表。
        """
        tx = target_pose.pose.position.x
        ty = target_pose.pose.position.y
        ideal_dist = self.arm_reach_max * self.ideal_reach_ratio

        scored = []
        for c in candidates:
            # 距离分：高斯
            dist = math.hypot(c.x - tx, c.y - ty)
            dist_score = math.exp(
                -0.5 * ((dist - ideal_dist) / self.reach_sigma) ** 2)

            # 朝向分：(1 + cos(diff)) / 2
            expected_yaw = math.atan2(ty - c.y, tx - c.x)
            diff = c.yaw - expected_yaw
            heading_score = (1.0 + math.cos(diff)) / 2.0

            total = (self.score_distance_weight * dist_score +
                     self.score_heading_weight * heading_score)
            scored.append((c, total))

        return scored

    def select_best(self, scored: list) -> Candidate:
        """从已评分列表中选出得分最高的候选。

        Args:
            scored: list[(Candidate, float)]，由 score() 返回。

        Returns:
            得分最高的 Candidate。

        Raises:
            ValueError: scored 为空列表。
        """
        if not scored:
            raise ValueError('scored 列表为空，无法选出最优候选')
        return max(scored, key=lambda item: item[1])[0]
