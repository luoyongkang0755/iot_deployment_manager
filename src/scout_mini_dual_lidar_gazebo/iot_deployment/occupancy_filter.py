"""候选基座位姿占据栅格过滤模块。

基于 /map (nav_msgs/OccupancyGrid) 检查候选位置周围
robot_radius 圆形范围内是否存在占据或未知栅格。
"""

import math
import logging

from nav_msgs.msg import OccupancyGrid

from iot_deployment import declare_param
from iot_deployment.candidate_generator import Candidate


class OccupancyFilter:
    """基于占据栅格地图的候选过滤器。

    支持两种构造方式：
      a) OccupancyFilter(node)：订阅 /map，从 ROS node 的 parameter 读取
      b) OccupancyFilter(node=None, robot_radius=..., map_required=...)：
         直接传参 + set_map() 注入地图，供单元测试使用
    """

    DEFAULTS = {
        'robot_radius': 0.25,
        'map_required': False,
    }

    def __init__(self, node=None, robot_radius=None, map_required=None):
        self._map = None
        if node is not None:
            self.robot_radius = declare_param(
                node, 'robot_radius', self.DEFAULTS['robot_radius'])
            self.map_required = declare_param(
                node, 'map_required', self.DEFAULTS['map_required'])
            self._logger = node.get_logger()
            node.create_subscription(
                OccupancyGrid, '/map', self._map_callback, 10)
        else:
            self.robot_radius = (
                robot_radius if robot_radius is not None
                else self.DEFAULTS['robot_radius'])
            self.map_required = (
                map_required if map_required is not None
                else self.DEFAULTS['map_required'])
            self._logger = logging.getLogger('OccupancyFilter')

        if self.robot_radius <= 0.0:
            raise ValueError('robot_radius 必须为正')

    def _map_callback(self, msg: OccupancyGrid):
        """保存最新地图。"""
        self._map = msg

    def set_map(self, msg: OccupancyGrid):
        """直接注入地图（供测试或外部调用）。"""
        self._map = msg

    def filter(self, candidates: list) -> list:
        """过滤候选位姿列表。

        对每个候选，检查其周围 robot_radius 圆形范围内的所有栅格：
        若存在占据（value > 50）或未知（value < 0）栅格，则拒绝该候选。

        地图未收到时：map_required=False 跳过检查并 warn，True 则拒绝全部。

        Args:
            candidates: list[Candidate]

        Returns:
            list[Candidate]，通过检查的候选。
        """
        if self._map is None:
            if self.map_required:
                self._logger.warning('地图未收到，map_required=true，拒绝全部候选')
                return []
            else:
                self._logger.warning('地图未收到，map_required=false，跳过占据检查')
                return list(candidates)

        info = self._map.info
        resolution = info.resolution
        width = info.width
        height = info.height
        ox = info.origin.position.x
        oy = info.origin.position.y
        data = self._map.data

        # robot_radius 对应的栅格数
        cell_radius = int(math.ceil(self.robot_radius / resolution))

        result = []
        for c in candidates:
            # 候选点所在栅格
            col = int((c.x - ox) / resolution)
            row = int((c.y - oy) / resolution)

            if not (0 <= col < width and 0 <= row < height):
                # 候选点在地图外，视为未知区域
                continue

            # 检查圆形范围内所有栅格
            if not self._circle_free(data, width, height, col, row,
                                     cell_radius, resolution):
                continue

            result.append(c)
        return result

    @staticmethod
    def _circle_free(data, width, height, col, row, cell_radius, resolution):
        """检查 (col, row) 周围 cell_radius 栅格圆内是否全部自由。"""
        r_sq = cell_radius * cell_radius
        for dr in range(-cell_radius, cell_radius + 1):
            for dc in range(-cell_radius, cell_radius + 1):
                if dr * dr + dc * dc > r_sq:
                    continue
                r = row + dr
                c = col + dc
                if not (0 <= r < height and 0 <= c < width):
                    # 超出地图边界视为未知
                    return False
                val = data[r * width + c]
                if val > 50 or val < 0:
                    return False
        return True
