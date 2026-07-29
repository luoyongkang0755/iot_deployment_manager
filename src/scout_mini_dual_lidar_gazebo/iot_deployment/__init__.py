"""IoT deployment Python 模块包。"""

from rclpy.exceptions import ParameterAlreadyDeclaredException


def declare_param(node, name, default):
    """declare_parameter 的幂等封装，允许多个模块声明同名参数。"""
    try:
        return node.declare_parameter(name, default).value
    except ParameterAlreadyDeclaredException:
        return node.get_parameter(name).value
