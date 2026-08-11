#!/usr/bin/env python3
"""纯 Python 正向运动学校准 pick pose（不依赖 Gazebo/rclpy）。

从 URDF 硬编码 Piper 的运动学链，网格搜索关节角，
找到 link7 最接近设备位置 (x=0.115, y=0, z=0.069) 的 pick pose。
所有关节严格在 URDF 限位内。

用法：
    python3 calibrate_pick_pose.py
"""
import itertools
import math
import numpy as np


# ============================================================
# Piper URDF 运动学链（从 piper_description.xacro 提取）
# 格式: (origin_xyz, origin_rpy, axis_xyz)
# ============================================================
JOINTS = [
    # piper_base_link -> link1 (joint1, base yaw)
    # origin xyz="0 0 0.123" rpy="0 0 0", axis "0 0 1"
    ([0, 0, 0.123], [0, 0, 0], [0, 0, 1]),
    # link1 -> link2 (joint2, shoulder pitch)
    # origin xyz="0 0 0" rpy="1.5708 -0.1359 -3.1416", axis "0 0 1"
    ([0, 0, 0], [1.5708, -0.1359, -3.1416], [0, 0, 1]),
    # link2 -> link3 (joint3, elbow pitch)
    # origin xyz="0.28503 0 0" rpy="0 0 -1.7939", axis "0 0 1"
    ([0.28503, 0, 0], [0, 0, -1.7939], [0, 0, 1]),
    # link3 -> link4 (joint4, wrist-1 pitch)
    # origin xyz="-0.021984 -0.25075 0" rpy="1.5708 0 0", axis "0 0 1"
    ([-0.021984, -0.25075, 0], [1.5708, 0, 0], [0, 0, 1]),
    # link4 -> link5 (joint5, wrist-2 roll)
    # origin xyz="0 0 0" rpy="-1.5708 0 0", axis "0 0 1"
    ([0, 0, 0], [-1.5708, 0, 0], [0, 0, 1]),
    # link5 -> link6 (joint6, flange yaw)
    # origin xyz="8.8259E-05 -0.091 0" rpy="1.5708 0 0", axis "0 0 1"
    ([8.8259e-05, -0.091, 0], [1.5708, 0, 0], [0, 0, 1]),
]

# link6 -> gripper_base (fixed joint, origin 0 0 0)
# gripper_base -> link7 (joint7 prismatic, origin xyz="0 0 0.1358" rpy="1.5708 0 0")
# 注意 joint7 是 prismatic 沿 z 轴。对于夹爪闭合位置 joint7≈0.004，
# 额外位移约 0.004m 沿 link7 局部 z 方向。
LINK7_ORIGIN = ([0, 0, 0.1358], [1.5708, 0, 0])
# joint7 位移 (gripper closed ≈ 0.004 m)
J7_OFFSET = 0.004

# piper_base_link 安装在 base_link 上方 chassis_top_z 处（piper_mount.xacro）。
# FK 输出在 piper_base_link 系，转 base_link 系需 z += PIPER_MOUNT_Z。
PIPER_MOUNT_Z = 0.054


def rpy_to_matrix(rpy):
    """Roll-Pitch-Yaw (XYZ extrinsic) -> 3x3 rotation matrix."""
    roll, pitch, yaw = rpy
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def axis_angle_to_matrix(axis, angle):
    """Axis-angle -> 3x3 rotation matrix (Rodrigues)."""
    ax = np.array(axis, dtype=float)
    ax = ax / np.linalg.norm(ax)
    x, y, z = ax
    c, s = math.cos(angle), math.sin(angle)
    C = 1 - c
    return np.array([
        [c + x * x * C, x * y * C - z * s, x * z * C + y * s],
        [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
        [z * x * C - y * s, z * y * C + x * s, c + z * z * C],
    ])


def fk(angles):
    """6-关节正向运动学。返回 link7 原点在 base_link 系中的 (x, y, z)。"""
    T = np.eye(4)
    for i, (xyz, rpy, axis) in enumerate(JOINTS):
        # 固定 origin 变换
        R_fixed = rpy_to_matrix(rpy)
        T_fixed = np.eye(4)
        T_fixed[:3, :3] = R_fixed
        T_fixed[:3, 3] = xyz
        # 关节旋转
        R_joint = axis_angle_to_matrix(axis, angles[i])
        T_joint = np.eye(4)
        T_joint[:3, :3] = R_joint
        T = T @ T_fixed @ T_joint

    # link6 -> gripper_base (fixed, identity)
    # gripper_base -> link7
    xyz7, rpy7 = LINK7_ORIGIN
    R7 = rpy_to_matrix(rpy7)
    T7 = np.eye(4)
    T7[:3, :3] = R7
    T7[:3, 3] = xyz7
    T = T @ T7
    # joint7 prismatic offset 沿 link7 的 z 轴
    T[:3, 3] += J7_OFFSET * T[:3, 2]
    # piper_base_link -> base_link: 只有 z 偏移
    x, y, z = T[0, 3], T[1, 3], T[2, 3] + PIPER_MOUNT_Z
    return (x, y, z)


def main():
    TARGET = np.array([0.115, 0.0, 0.069])

    # 关节限位（来自 URDF）
    LIM = {
        1: (-2.618, 2.618),
        2: (0, 3.14),
        3: (-2.967, 0),
        4: (-1.745, 1.745),
        5: (-1.22, 1.22),
        6: (-2.0944, 2.0944),
    }

    # 网格搜索：j1=0 正前方
    # j2 (shoulder): 控制大臂俯仰，0=直立 .. 1.57=水平向前 .. 3.14=向后
    # j3 (elbow):    控制小臂弯曲，0=直 .. -2.967=完全折回
    # j4 (wrist-1):  小幅调整
    # j5 (wrist-2):  小幅调整
    j1_vals = [0.0]
    j2_vals = np.arange(0.6, 2.41, 0.2).round(2)
    j3_vals = np.arange(-0.4, -2.81, -0.2).round(2)
    j4_vals = [0.0]
    j5_vals = np.arange(-1.2, 1.21, 0.3).round(2)
    j6_vals = [0.0]

    results = []
    total = len(j1_vals) * len(j2_vals) * len(j3_vals) * len(j5_vals)
    print(f'扫描 {total} 个候选 ...')

    for j1, j2, j3, j5 in itertools.product(j1_vals, j2_vals, j3_vals, j5_vals):
        angles = [j1, j2, j3, 0.0, j5, 0.0]
        x, y, z = fk(angles)
        err = math.sqrt((x - TARGET[0])**2 + (y - TARGET[1])**2 + (z - TARGET[2])**2)
        results.append((err, angles, x, y, z))

    results.sort(key=lambda r: r[0])
    print('\n' + '=' * 70)
    print('  TOP 10 PICK POSE 候选（纯 FK 计算）')
    print('=' * 70)
    print(f'  目标 (base_link): x={TARGET[0]} y={TARGET[1]} z={TARGET[2]}')
    print('-' * 70)
    for i, (err, pose, x, y, z) in enumerate(results[:10]):
        print(f'  #{i+1}  err={err*100:.1f} cm')
        print(f'      pose: [{pose[0]:.2f}, {pose[1]:.2f}, {pose[2]:.2f}, '
              f'{pose[3]:.2f}, {pose[4]:.2f}, {pose[5]:.2f}]')
        print(f'      link7: x={x:.4f} y={y:.4f} z={z:.4f}')
        dx = x - TARGET[0]; dy = y - TARGET[1]; dz = z - TARGET[2]
        print(f'      delta: dx={dx:+.4f} dy={dy:+.4f} dz={dz:+.4f}')
    print('=' * 70)

    # 自动生成 pick_above（在 pick 基础上抬肩部、伸肘部）
    if results:
        best_err, best_pose, *_ = results[0]
        print(f'\n推荐 pick pose: {best_pose}  (err={best_err*100:.1f} cm)')
        j2_above = min(best_pose[1] + 0.5, LIM[2][1])
        j3_above = min(best_pose[2] + 0.5, LIM[3][1])
        above = [0.0, round(j2_above, 2), round(j3_above, 2), 0.0,
                 round(best_pose[4], 2), 0.0]
        x, y, z = fk(above)
        print(f'推荐 pick_above: {above}')
        print(f'  (link7 在上方: x={x:.4f} y={y:.4f} z={z:.4f})')


if __name__ == '__main__':
    main()
