#!/usr/bin/env python3
"""IoT 自主部署端到端连跑基准测试脚本。

自动执行 N 轮完整链路（取货 -> 导航 -> 放置），从 launch 日志中提取
各阶段时间戳（wall time），统计成功率与耗时，输出 CSV 供论文/汇报使用。

用法（宿主机运行）:
    python3 scripts/benchmark_run.py [轮数] [CSV输出路径]

默认 10 轮，输出 benchmark_results.csv。
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

CONTAINER = 'scout_nav2'
LAUNCH_CMD = (
    "source /ws/install/setup.bash && "
    "ros2 launch scout_mini_dual_lidar_gazebo iot_deployment_launch.py"
)
# 单轮整体超时（秒）。Gazebo 启动 + controllers + 取货 + 导航 + 放置。
TIMEOUT = 360.0
# docker restart 后的等待时间（秒）。
RESTART_SETTLE = 5.0

# 日志关键字 -> 事件名。按时间先后匹配，每个事件只记录第一次出现。
EVENTS = [
    ('pick_start',  '取货流程开始（第'),
    ('pick_done',   '取货完成，机械臂处于携带位'),
    ('nav_start',   'Begin navigating from current location'),
    ('nav_done',    '导航成功，发布 READY_FOR_MANIPULATION'),
    ('place_start', '放置流程开始'),
    ('place_done',  '放置完成，发布 DEPLOYMENT_COMPLETE'),
]

CSV_FIELDS = [
    'run', 'result',
    'pick_start', 'pick_done', 'pick_dur',
    'nav_start', 'nav_done', 'nav_dur',
    'place_start', 'place_done', 'place_dur',
    'total_dur',
]


def run_docker(args, check=True):
    return subprocess.run(
        ['docker'] + args, capture_output=True, text=True, check=check)


def restart_container():
    print('  [restart] docker restart', CONTAINER)
    run_docker(['restart', CONTAINER])
    time.sleep(RESTART_SETTLE)


def launch_and_collect():
    """启动一次 launch，实时读日志，返回 (result, 各事件 wall-time 秒)。"""
    t0 = time.time()
    events = {}  # 事件名 -> 相对 t0 的秒数

    cmd = ['docker', 'exec', '-t', CONTAINER, 'bash', '-c', LAUNCH_CMD]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    result = 'timeout'
    try:
        for line in proc.stdout:
            now = time.time() - t0
            for name, keyword in EVENTS:
                if name not in events and keyword in line:
                    events[name] = round(now, 2)
            if 'MANIPULATION_FAILED' in line:
                result = 'MANIPULATION_FAILED'
                break
            if 'DEPLOYMENT_FAILED' in line:
                result = 'DEPLOYMENT_FAILED'
                break
            if 'place_done' in events:
                result = 'DEPLOYMENT_COMPLETE'
                break
            if now > TIMEOUT:
                result = 'timeout'
                break
    finally:
        proc.stdout.close()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    return result, events


def main():
    n_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    out_path = sys.argv[2] if len(sys.argv) > 2 else 'benchmark_results.csv'

    print(f'=== IoT 部署连跑基准测试：{n_runs} 轮，超时 {TIMEOUT}s/轮 ===')

    rows = []
    success = 0
    for run in range(1, n_runs + 1):
        print(f'\n--- 第 {run}/{n_runs} 轮 ---')
        restart_container()
        result, ev = launch_and_collect()

        if result == 'DEPLOYMENT_COMPLETE':
            success += 1

        row = {
            'run': run,
            'result': result,
            'pick_start': ev.get('pick_start', ''),
            'pick_done': ev.get('pick_done', ''),
            'pick_dur': _dur(ev, 'pick_start', 'pick_done'),
            'nav_start': ev.get('nav_start', ''),
            'nav_done': ev.get('nav_done', ''),
            'nav_dur': _dur(ev, 'nav_start', 'nav_done'),
            'place_start': ev.get('place_start', ''),
            'place_done': ev.get('place_done', ''),
            'place_dur': _dur(ev, 'place_start', 'place_done'),
            'total_dur': _dur(ev, 'pick_start', 'place_done'),
        }
        rows.append(row)
        print(f'  结果: {result} | 取货 {row["pick_dur"]}s | '
              f'导航 {row["nav_dur"]}s | 放置 {row["place_dur"]}s')

        # 清理残留进程，准备下一轮
        restart_container()

    # 写入 CSV
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    rate = success / n_runs * 100
    print(f'\n=== 完成 ===')
    print(f'成功率: {success}/{n_runs} = {rate:.1f}%')
    print(f'结果已写入: {out_path}')


def _dur(ev, start_key, end_key):
    s = ev.get(start_key)
    e = ev.get(end_key)
    if s is not None and e is not None:
        return round(e - s, 2)
    return ''


if __name__ == '__main__':
    main()
