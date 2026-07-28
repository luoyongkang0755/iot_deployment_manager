"""CandidateGenerator 单元测试（不依赖 rclpy 节点上下文）。

运行：
    pytest /ws/src/scout_mini_dual_lidar_gazebo/test/test_candidate_generator.py
"""

import math

import pytest

from iot_deployment.candidate_generator import Candidate, CandidateGenerator


def make_target(x=1.0, y=2.0):
    """构造 geometry_msgs/PoseStamped 目标位姿。"""
    from geometry_msgs.msg import PoseStamped
    msg = PoseStamped()
    msg.header.frame_id = 'map'
    msg.pose.position.x = x
    msg.pose.position.y = y
    msg.pose.position.z = 0.0
    msg.pose.orientation.w = 1.0
    return msg


ARM_REACH_MIN = 0.20
ARM_REACH_MAX = 0.60
RADIUS_COUNT = 3
ANGLE_STEP = 30.0
TARGET = make_target()


@pytest.fixture
def generator():
    return CandidateGenerator(
        node=None,
        arm_reach_min=ARM_REACH_MIN,
        arm_reach_max=ARM_REACH_MAX,
        radius_count=RADIUS_COUNT,
        angle_step=ANGLE_STEP,
    )


def test_candidate_count(generator):
    """候选总数 == radius_count * (360 / angle_step)。"""
    candidates = generator.generate(TARGET)
    expected = RADIUS_COUNT * int(round(360.0 / ANGLE_STEP))
    assert len(candidates) == expected
    assert expected == 36


def test_distance_within_reach(generator):
    """每个候选到目标的 2D 距离在 [arm_reach_min, arm_reach_max] 内。"""
    candidates = generator.generate(TARGET)
    for c in candidates:
        dist = math.hypot(c.x - TARGET.pose.position.x,
                          c.y - TARGET.pose.position.y)
        assert ARM_REACH_MIN - 1e-9 <= dist <= ARM_REACH_MAX + 1e-9


def test_radii_cover_range(generator):
    """候选圈半径应覆盖 [min, max]（含端点）。"""
    candidates = generator.generate(TARGET)
    dists = {round(math.hypot(c.x - TARGET.pose.position.x,
                              c.y - TARGET.pose.position.y), 9)
             for c in candidates}
    assert round(ARM_REACH_MIN, 9) in dists
    assert round(ARM_REACH_MAX, 9) in dists
    assert len(dists) == RADIUS_COUNT


def test_yaw_faces_target(generator):
    """每个候选 yaw 朝向目标，误差 < 5 度。"""
    candidates = generator.generate(TARGET)
    for c in candidates:
        expected_yaw = math.atan2(TARGET.pose.position.y - c.y,
                                  TARGET.pose.position.x - c.x)
        err = abs(math.atan2(math.sin(c.yaw - expected_yaw),
                             math.cos(c.yaw - expected_yaw)))
        assert err < math.radians(5.0)


def test_yaw_is_normalized(generator):
    """yaw 在 [-pi, pi] 范围内。"""
    candidates = generator.generate(TARGET)
    for c in candidates:
        assert -math.pi <= c.yaw <= math.pi


def test_target_at_origin():
    """目标在原点时同样成立。"""
    gen = CandidateGenerator(node=None, arm_reach_min=0.3, arm_reach_max=0.5,
                             radius_count=2, angle_step=45.0)
    target = make_target(0.0, 0.0)
    candidates = gen.generate(target)
    assert len(candidates) == 2 * int(round(360.0 / 45.0))
    for c in candidates:
        dist = math.hypot(c.x, c.y)
        assert 0.3 - 1e-9 <= dist <= 0.5 + 1e-9
        expected_yaw = math.atan2(-c.y, -c.x)
        err = abs(math.atan2(math.sin(c.yaw - expected_yaw),
                             math.cos(c.yaw - expected_yaw)))
        assert err < math.radians(5.0)


def test_single_ring():
    """radius_count=1 时取最大半径。"""
    gen = CandidateGenerator(node=None, arm_reach_min=0.2, arm_reach_max=0.6,
                             radius_count=1, angle_step=90.0)
    candidates = gen.generate(TARGET)
    assert len(candidates) == 4
    for c in candidates:
        dist = math.hypot(c.x - TARGET.pose.position.x,
                          c.y - TARGET.pose.position.y)
        assert dist == pytest.approx(0.6, abs=1e-9)


def test_invalid_params():
    """非法参数抛出 ValueError。"""
    with pytest.raises(ValueError):
        CandidateGenerator(node=None, arm_reach_min=0.0)
    with pytest.raises(ValueError):
        CandidateGenerator(node=None, arm_reach_min=0.6, arm_reach_max=0.2)
    with pytest.raises(ValueError):
        CandidateGenerator(node=None, radius_count=0)
    with pytest.raises(ValueError):
        CandidateGenerator(node=None, angle_step=0.0)
    with pytest.raises(ValueError):
        CandidateGenerator(node=None, angle_step=400.0)


def test_candidate_dataclass():
    """Candidate dataclass 字段为 float。"""
    c = Candidate(x=1.0, y=2.0, yaw=0.5)
    assert isinstance(c.x, float)
    assert isinstance(c.y, float)
    assert isinstance(c.yaw, float)
