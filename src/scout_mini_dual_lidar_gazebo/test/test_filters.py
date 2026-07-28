"""阶段3过滤器与评分器单元测试（不依赖 rclpy 节点上下文）。

运行：
    pytest /ws/src/scout_mini_dual_lidar_gazebo/test/test_filters.py
"""

import math

import pytest

from iot_deployment.candidate_generator import Candidate
from iot_deployment.reachability_filter import ReachabilityFilter
from iot_deployment.occupancy_filter import OccupancyFilter
from iot_deployment.candidate_scorer import CandidateScorer


def make_target(x=1.0, y=2.0, z=0.3):
    """构造 geometry_msgs/PoseStamped 目标位姿。"""
    from geometry_msgs.msg import PoseStamped
    msg = PoseStamped()
    msg.header.frame_id = 'map'
    msg.pose.position.x = x
    msg.pose.position.y = y
    msg.pose.position.z = z
    msg.pose.orientation.w = 1.0
    return msg


def make_candidate(x, y, yaw=0.0):
    return Candidate(x=x, y=y, yaw=yaw)


# ======================== ReachabilityFilter ========================

ARM_REACH_MIN = 0.20
ARM_REACH_MAX = 0.60
BASE_LINK_Z = 0.054
GRIPPER_Z_OFFSET = 0.267
HEIGHT_TOLERANCE = 0.1
# gripper 实际 z = 0.054 + 0.267 = 0.321
GRIPPER_Z = BASE_LINK_Z + GRIPPER_Z_OFFSET


@pytest.fixture
def reach_filter():
    return ReachabilityFilter(
        node=None,
        arm_reach_min=ARM_REACH_MIN,
        arm_reach_max=ARM_REACH_MAX,
        base_link_z=BASE_LINK_Z,
        gripper_z_offset=GRIPPER_Z_OFFSET,
        height_tolerance=HEIGHT_TOLERANCE,
    )


class TestReachabilityFilter:

    def test_distance_in_range_kept(self, reach_filter):
        """距离在 [min, max] 内的候选保留。"""
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z)
        # 距离 0.4，在 [0.2, 0.6] 内
        c = make_candidate(x=0.4, y=0.0)
        result = reach_filter.filter([c], target)
        assert len(result) == 1

    def test_distance_too_close_rejected(self, reach_filter):
        """距离 < arm_reach_min 的候选被拒绝。"""
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z)
        c = make_candidate(x=0.1, y=0.0)  # 距离 0.1 < 0.2
        result = reach_filter.filter([c], target)
        assert len(result) == 0

    def test_distance_too_far_rejected(self, reach_filter):
        """距离 > arm_reach_max 的候选被拒绝。"""
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z)
        c = make_candidate(x=0.7, y=0.0)  # 距离 0.7 > 0.6
        result = reach_filter.filter([c], target)
        assert len(result) == 0

    def test_height_out_of_tolerance_all_rejected(self, reach_filter):
        """目标 z 超出容差时返回空列表。"""
        # gripper_z = 0.321，目标 z = 0.321 + 0.15 = 0.471，超出 tol=0.1
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z + HEIGHT_TOLERANCE + 0.05)
        c = make_candidate(x=0.4, y=0.0)
        result = reach_filter.filter([c], target)
        assert result == []

    def test_height_within_tolerance_kept(self, reach_filter):
        """目标 z 在容差内时正常过滤。"""
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z + HEIGHT_TOLERANCE - 0.01)
        c = make_candidate(x=0.4, y=0.0)
        result = reach_filter.filter([c], target)
        assert len(result) == 1

    def test_mixed_candidates(self, reach_filter):
        """混合候选：只有满足距离和高度条件的保留。"""
        target = make_target(x=0.0, y=0.0, z=GRIPPER_Z)
        candidates = [
            make_candidate(x=0.1, y=0.0),   # 太近
            make_candidate(x=0.4, y=0.0),   # 合适
            make_candidate(x=0.0, y=0.5),   # 合适
            make_candidate(x=0.8, y=0.0),   # 太远
        ]
        result = reach_filter.filter(candidates, target)
        assert len(result) == 2


# ======================== OccupancyFilter ========================

ROBOT_RADIUS = 0.25


def _make_occupancy_grid(width=20, height=20, resolution=0.05,
                         origin_x=0.0, origin_y=0.0,
                         occupied_cells=None, unknown_cells=None):
    """构造测试用 OccupancyGrid。

    Args:
        occupied_cells: list of (col, row) 设为 100
        unknown_cells: list of (col, row) 设为 -1
    """
    from nav_msgs.msg import OccupancyGrid
    msg = OccupancyGrid()
    msg.info.resolution = resolution
    msg.info.width = width
    msg.info.height = height
    msg.info.origin.position.x = origin_x
    msg.info.origin.position.y = origin_y
    msg.info.origin.orientation.w = 1.0
    data = [0] * (width * height)
    if occupied_cells:
        for col, row in occupied_cells:
            data[row * width + col] = 100
    if unknown_cells:
        for col, row in unknown_cells:
            data[row * width + col] = -1
    msg.data = data
    return msg


@pytest.fixture
def occ_filter():
    return OccupancyFilter(node=None, robot_radius=ROBOT_RADIUS,
                           map_required=False)


class TestOccupancyFilter:

    def test_free_area_kept(self, occ_filter):
        """自由区域内的候选保留。"""
        grid = _make_occupancy_grid()
        occ_filter.set_map(grid)
        # 候选在 (0.5, 0.5) → col=10, row=10，周围无占据
        c = make_candidate(x=0.5, y=0.5)
        result = occ_filter.filter([c])
        assert len(result) == 1

    def test_occupied_cell_rejected(self, occ_filter):
        """候选位置有占据栅格时被拒绝。"""
        # 在 col=10, row=10 放占据
        grid = _make_occupancy_grid(occupied_cells=[(10, 10)])
        occ_filter.set_map(grid)
        # 候选在 (0.5, 0.5) → col=10, row=10
        c = make_candidate(x=0.5, y=0.5)
        result = occ_filter.filter([c])
        assert len(result) == 0

    def test_occupied_nearby_rejected(self, occ_filter):
        """候选附近 robot_radius 内有占据时被拒绝。"""
        # robot_radius=0.25, resolution=0.05 → cell_radius=5
        # 在 col=13, row=10 放占据，距候选 (10,10) 仅 3 格（在范围内）
        grid = _make_occupancy_grid(occupied_cells=[(13, 10)])
        occ_filter.set_map(grid)
        c = make_candidate(x=0.5, y=0.5)
        result = occ_filter.filter([c])
        assert len(result) == 0

    def test_unknown_cell_rejected(self, occ_filter):
        """未知栅格（value=-1）也会被拒绝。"""
        grid = _make_occupancy_grid(unknown_cells=[(10, 10)])
        occ_filter.set_map(grid)
        c = make_candidate(x=0.5, y=0.5)
        result = occ_filter.filter([c])
        assert len(result) == 0

    def test_far_obstacle_kept(self, occ_filter):
        """距离候选超过 robot_radius 的占据不影响。"""
        # cell_radius=5，在 (16, 10) 放占据，距 (10,10) 有 6 格 > 5
        grid = _make_occupancy_grid(occupied_cells=[(16, 10)])
        occ_filter.set_map(grid)
        c = make_candidate(x=0.5, y=0.5)
        result = occ_filter.filter([c])
        assert len(result) == 1

    def test_no_map_not_required_keeps_all(self):
        """无地图且 map_required=false 时跳过检查。"""
        f = OccupancyFilter(node=None, robot_radius=ROBOT_RADIUS,
                            map_required=False)
        candidates = [make_candidate(x=0.5, y=0.5)]
        result = f.filter(candidates)
        assert len(result) == 1

    def test_no_map_required_rejects_all(self):
        """无地图且 map_required=true 时拒绝全部。"""
        f = OccupancyFilter(node=None, robot_radius=ROBOT_RADIUS,
                            map_required=True)
        candidates = [make_candidate(x=0.5, y=0.5)]
        result = f.filter(candidates)
        assert result == []

    def test_out_of_map_rejected(self, occ_filter):
        """候选点在地图边界外被拒绝。"""
        grid = _make_occupancy_grid()
        occ_filter.set_map(grid)
        c = make_candidate(x=5.0, y=5.0)  # 地图只有 1m x 1m
        result = occ_filter.filter([c])
        assert len(result) == 0


# ======================== CandidateScorer ========================

SCORER_REACH_MAX = 0.60
IDEAL_REACH_RATIO = 0.7
REACH_SIGMA = 0.1
DIST_WEIGHT = 0.6
HEAD_WEIGHT = 0.4
# 理想距离 = 0.60 * 0.7 = 0.42
IDEAL_DIST = SCORER_REACH_MAX * IDEAL_REACH_RATIO


@pytest.fixture
def scorer():
    return CandidateScorer(
        node=None,
        arm_reach_max=SCORER_REACH_MAX,
        ideal_reach_ratio=IDEAL_REACH_RATIO,
        reach_sigma=REACH_SIGMA,
        score_distance_weight=DIST_WEIGHT,
        score_heading_weight=HEAD_WEIGHT,
    )


def _make_oriented_candidate(target_x, target_y, dist, angle_offset=0.0):
    """在目标周围指定距离处生成 yaw 精确朝向目标的候选。

    Args:
        angle_offset: 在精确朝向的基础上额外加的偏角（弧度）。
    """
    # 候选在目标正右方 dist 处
    cx = target_x + dist
    cy = target_y
    yaw = math.atan2(target_y - cy, target_x - cx) + angle_offset
    return Candidate(x=cx, y=cy, yaw=yaw)


class TestCandidateScorer:

    def test_ideal_distance_scores_higher(self, scorer):
        """理想距离候选得分 > 过近/过远候选（朝向相同）。"""
        target = make_target(x=0.0, y=0.0, z=0.3)
        ideal = _make_oriented_candidate(0.0, 0.0, IDEAL_DIST)
        too_close = _make_oriented_candidate(0.0, 0.0, 0.25)
        too_far = _make_oriented_candidate(0.0, 0.0, 0.58)

        scored = scorer.score([ideal, too_close, too_far], target)
        scores = {id(c): s for c, s in scored}
        assert scores[id(ideal)] > scores[id(too_close)]
        assert scores[id(ideal)] > scores[id(too_far)]

    def test_heading_perfect_scores_higher(self, scorer):
        """朝向完美（diff=0）得分 > 朝向偏差大（同距离）。"""
        target = make_target(x=0.0, y=0.0, z=0.3)
        perfect = _make_oriented_candidate(0.0, 0.0, IDEAL_DIST, angle_offset=0.0)
        deviated = _make_oriented_candidate(0.0, 0.0, IDEAL_DIST,
                                            angle_offset=math.radians(90))

        scored = scorer.score([perfect, deviated], target)
        scores = {id(c): s for c, s in scored}
        assert scores[id(perfect)] > scores[id(deviated)]

    def test_score_range(self, scorer):
        """总分应在 [0, dist_weight + head_weight] 范围内。"""
        target = make_target(x=0.0, y=0.0, z=0.3)
        c = _make_oriented_candidate(0.0, 0.0, IDEAL_DIST)
        scored = scorer.score([c], target)
        total = scored[0][1]
        assert 0.0 <= total <= DIST_WEIGHT + HEAD_WEIGHT

    def test_select_best_returns_highest(self, scorer):
        """select_best 返回得分最高的候选。"""
        target = make_target(x=0.0, y=0.0, z=0.3)
        candidates = [
            _make_oriented_candidate(0.0, 0.0, 0.25),        # 过近
            _make_oriented_candidate(0.0, 0.0, IDEAL_DIST),   # 理想
            _make_oriented_candidate(0.0, 0.0, 0.58),         # 过远
        ]
        scored = scorer.score(candidates, target)
        best = scorer.select_best(scored)
        assert best is candidates[1]

    def test_select_best_empty_raises(self, scorer):
        """select_best 空列表抛 ValueError。"""
        with pytest.raises(ValueError):
            scorer.select_best([])
