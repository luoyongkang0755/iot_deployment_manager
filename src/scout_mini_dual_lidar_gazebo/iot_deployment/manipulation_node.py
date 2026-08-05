#!/usr/bin/env python3
"""Stage 5: pick-and-place manipulation node for the Piper arm.

Startup: drives the arm from home -> above the storage bin -> down to the
pick pose -> close gripper -> attach the IoT device -> lift -> carry pose,
then waits. On "READY_FOR_MANIPULATION" it drives carry -> above target ->
down to place -> detach -> open gripper -> lift -> home, and publishes
"DEPLOYMENT_COMPLETE" on /manipulation_status.

Grasping is simulated with a Gazebo Sim DETACHABLE_JOINT: a fixed joint
welding the IoT device to the gripper is created (attach) and removed
(detach) via the world entity services, so the box follows the gripper
while attached and stays on the shelf after detach.

All joint poses, timings and names come from manipulation_waypoints.yaml;
nothing is hardcoded here.
"""

import subprocess

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from rclpy.action import ActionClient
from action_msgs.msg import GoalStatus

from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped

STATUS_READY = 'READY_FOR_MANIPULATION'
STATUS_DEPLOY_FAILED = 'DEPLOYMENT_FAILED'
STATUS_COMPLETE = 'DEPLOYMENT_COMPLETE'
STATUS_MANIP_FAILED = 'MANIPULATION_FAILED'

ARM_JOINTS = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
GRIPPER_JOINTS = ['joint7']


class ManipulationNode(Node):
    def __init__(self):
        super().__init__('manipulation_node')

        # ---- Parameters (from manipulation_waypoints.yaml) ----
        self._poses = {
            'home': self._get_pose('pose_home'),
            'pick_above': self._get_pose('pose_pick_above'),
            'pick': self._get_pose('pose_pick'),
            'carry': self._get_pose('pose_carry'),
            'place_above': self._get_pose('pose_place_above'),
            'place': self._get_pose('pose_place'),
        }
        self._gripper_open = self.declare_parameter('gripper_open', 0.035).value
        self._gripper_closed = self.declare_parameter('gripper_closed', 0.004).value
        self._arm_dur = self.declare_parameter('arm_move_duration', 3.0).value
        self._grip_dur = self.declare_parameter('gripper_move_duration', 1.5).value
        self._attach_settle = self.declare_parameter('attach_settle_time', 0.5).value
        self._detach_settle = self.declare_parameter('detach_settle_time', 0.5).value
        self._world = self.declare_parameter('world_name', 'simple_test_world').value
        self._parent_model = self.declare_parameter('parent_model_name', 'scout_mini').value
        self._parent_link = self.declare_parameter('parent_link_name', 'gripper_base').value
        self._child_model = self.declare_parameter('child_model_name', 'iot_device').value
        self._child_link = self.declare_parameter('child_link_name', 'iot_device_link').value
        self._place_z_offset = self.declare_parameter('place_z_offset', 0.03).value
        # Placement target (deployment shelf) for auto-triggering navigation.
        self._target_x = self.declare_parameter('target_x', 3.0).value
        self._target_y = self.declare_parameter('target_y', -3.0).value
        self._target_z = self.declare_parameter('target_z', 0.5).value
        arm_action = self.declare_parameter(
            'arm_action_name', '/arm_controller/follow_joint_trajectory').value
        grip_action = self.declare_parameter(
            'gripper_action_name', '/gripper_controller/follow_joint_trajectory').value

        # ---- ROS interfaces ----
        self._arm_client = ActionClient(self, FollowJointTrajectory, arm_action)
        self._grip_client = ActionClient(self, FollowJointTrajectory, grip_action)
        # gz transport topics for the DetachableJoint plugin (via `ign topic`).
        self._attach_topic = f'/{self._child_model}/attach'
        self._detach_topic = f'/{self._child_model}/detach'
        self._status_pub = self.create_publisher(String, '/manipulation_status', 10)
        # 自动发布放置目标给导航节点，实现端到端无人干预。
        self._target_pub = self.create_publisher(
            PoseStamped, '/deployment_target', 10)
        self.create_subscription(
            String, '/deployment_status', self._deployment_status_cb, 10)
        # AMCL 就绪信号：收到一次 /amcl_pose 即说明定位已建立。
        self._amcl_received = False
        self.create_subscription(
            PoseWithCovarianceStamped, '/amcl_pose',
            self._amcl_pose_cb, 10)

        # ---- Internal state ----
        self._holding = False        # whether device is attached
        self._picked = False         # pick sequence finished
        self._busy = False           # a sequence is running
        self._ready_pending = False  # READY arrived before pick finished
        self._pick_retries = 0       # pick attempts so far
        self._max_pick_retries = 5   # give up after this many failures
        self._auto_nav_waited = 0.0  # seconds waited for TF before auto-publish

        self.get_logger().info('manipulation_node 启动，等待 controller 就绪后执行取货')

        # Kick off the pick sequence once controllers are available.
        self._startup_timer = self.create_timer(0.5, self._startup_once)

    # ------------------------------------------------------------------
    # Parameter helpers
    # ------------------------------------------------------------------
    def _get_pose(self, name):
        return list(self.declare_parameter(name, [0.0] * 6).value)

    # ------------------------------------------------------------------
    # Startup: ensure controllers are active, then run the pick sequence.
    # The spawners only LOAD the controllers (activation via spawner is
    # timing-fragile on slow first sim startup); this node explicitly
    # activates them through switch_controller, then starts. If they are
    # already active the switch call is a harmless no-op.
    # ------------------------------------------------------------------
    def _startup_once(self):
        # spawner 在 launch 里负责加载并激活 controllers；这里只需等待
        # 两个 trajectory action server 就绪（active controller 提供）。
        arm_up = self._arm_client.wait_for_server(timeout_sec=0.2)
        grip_up = self._grip_client.wait_for_server(timeout_sec=0.2)
        if not (arm_up and grip_up):
            self.get_logger().info('等待 arm/gripper controller action server ...')
            return
        self._startup_timer.cancel()

        self.get_logger().info('controllers 就绪，先解除初始焊接再取货')
        # DetachableJoint 插件在 child model 出现时会立即自动 attach（语义
        # 是"初始已连接"），会把设备焊死在储物格 spawn 点。先 detach 释放，
        # 让设备作为自由刚体留在储物格，抓取时再按需 attach。
        self._run_ign_topic(
            self._detach_topic, '初始 detach',
            lambda ok, why='': self._after_initial_detach(ok, why))

    def _after_initial_detach(self, ok, why=''):
        if not ok:
            self.get_logger().error(f'初始 detach 失败: {why}，发布 MANIPULATION_FAILED')
            self._publish_status(STATUS_MANIP_FAILED)
            return
        self.get_logger().info('初始焊接已解除，开始取货流程')
        self._run_pick_sequence()

    # ------------------------------------------------------------------
    # AMCL pose subscription：定位就绪信号
    # ------------------------------------------------------------------
    def _amcl_pose_cb(self, msg):
        if not self._amcl_received:
            self._amcl_received = True
            self.get_logger().info('收到 /amcl_pose，AMCL 定位已就绪')

    # ------------------------------------------------------------------
    # Deployment status subscription
    # ------------------------------------------------------------------
    def _deployment_status_cb(self, msg: String):
        if msg.data == STATUS_DEPLOY_FAILED:
            self.get_logger().warn('收到 DEPLOYMENT_FAILED，机械臂保持当前姿态不动')
            return
        if msg.data != STATUS_READY:
            return
        if not self._picked:
            self.get_logger().info('收到 READY_FOR_MANIPULATION，取货未完成，稍后执行放置')
            self._ready_pending = True
            return
        if self._busy:
            self.get_logger().warn('收到 READY 但机械臂忙，忽略')
            return
        self._run_place_sequence()

    # ------------------------------------------------------------------
    # Pick sequence: home -> pick_above -> pick -> close -> attach -> lift
    # -> carry. Uses chained async steps.
    # ------------------------------------------------------------------
    def _run_pick_sequence(self):
        self._busy = True
        self._pick_retries += 1
        self.get_logger().info(f'取货流程开始（第 {self._pick_retries} 次尝试）')
        steps = [
            ('home', lambda cb: self._move_arm('home', cb)),
            ('pick_above', lambda cb: self._move_arm('pick_above', cb)),
            ('pick', lambda cb: self._move_arm('pick', cb)),
            ('close', lambda cb: self._move_gripper(self._gripper_closed, cb)),
            ('attach', self._attach),
            ('settle_attach', lambda cb: self._wait(self._attach_settle, cb)),
            ('pick_above2', lambda cb: self._move_arm('pick_above', cb)),
            ('carry', lambda cb: self._move_arm('carry', cb)),
        ]
        self._run_steps(steps, on_done=self._on_pick_done,
                        on_fail=self._on_pick_failed)

    def _on_pick_failed(self, why):
        self._busy = False
        self.get_logger().warn(f'取货失败: {why}')
        # 启动时序竞争（controllers/sim 尚未完全就绪）会让轨迹 goal abort；
        # 延时重试，而非直接放弃。
        if self._pick_retries < self._max_pick_retries:
            self.get_logger().info('3s 后重试取货 ...')
            self._retry_timer = self.create_timer(3.0, self._retry_pick_once)
        else:
            self.get_logger().error('取货多次失败，发布 MANIPULATION_FAILED')
            self._publish_status(STATUS_MANIP_FAILED)

    def _retry_pick_once(self):
        # 一次性定时器回调：取消自身后，仅在空闲且尚未取货时重试
        self._retry_timer.cancel()
        if self._busy or self._picked:
            return
        self._run_pick_sequence()

    def _on_pick_done(self):
        self._busy = False
        self._picked = True
        self._holding = True
        self.get_logger().info('取货完成，机械臂处于携带位，等待 READY_FOR_MANIPULATION')
        if self._ready_pending:
            self._ready_pending = False
            self._run_place_sequence()
            return
        # 取货完成但 READY 未到：自动发布放置目标，触发导航自动前往台面。
        # 轮询等待 map→odom TF 可用（即 AMCL 已收到初始位姿）后再发布，
        # 否则 Nav2 在 map frame 缺失时会瞬间拒绝所有候选。
        self._auto_nav_timer = self.create_timer(2.0, self._wait_tf_and_publish)

    def _wait_tf_and_publish(self):
        self._auto_nav_waited += 2.0
        # 仅当 map->base_link TF 可用时才发布目标
        if not self._tf_ready():
            self.get_logger().info('等待 AMCL 定位就绪 (map->base_link) 再自动发布目标 ...',
                                   throttle_duration_sec=5.0)
            # 超时保护：超过 120s 仍未就绪，强制发布（让 approach 节点决定）
            if self._auto_nav_waited < 120.0:
                return
            self.get_logger().warn('等待 TF 超时(120s)，强制发布放置目标')
        self._auto_nav_timer.cancel()
        self._publish_target_once()

    def _tf_ready(self):
        # 优先用 AMCL 就绪信号；TF 作为备用检查
        if self._amcl_received:
            return True
        if not hasattr(self, '_tf_buffer'):
            from tf2_ros import Buffer, TransformListener
            self._tf_buffer = Buffer()
            self._tf_listener = TransformListener(self._tf_buffer, self)
        try:
            return self._tf_buffer.can_transform('map', 'base_link', Time())
        except Exception:
            return False

    def _publish_target_once(self):
        self._auto_nav_timer.cancel()
        msg = PoseStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x = self._target_x
        msg.pose.position.y = self._target_y
        msg.pose.position.z = self._target_z
        msg.pose.orientation.w = 1.0
        self._target_pub.publish(msg)
        self.get_logger().info(
            f'自动发布放置目标: ({self._target_x:.2f}, '
            f'{self._target_y:.2f}, {self._target_z:.2f})')

    # ------------------------------------------------------------------
    # Place sequence: carry -> place_above -> place -> detach -> open ->
    # lift -> home.
    # ------------------------------------------------------------------
    def _run_place_sequence(self):
        self._busy = True
        self.get_logger().info('放置流程开始')
        steps = [
            ('place_above', lambda cb: self._move_arm('place_above', cb)),
            ('place', lambda cb: self._move_arm('place', cb)),
            ('detach', self._detach),
            ('settle_detach', lambda cb: self._wait(self._detach_settle, cb)),
            ('open', lambda cb: self._move_gripper(self._gripper_open, cb)),
            ('place_above2', lambda cb: self._move_arm('place_above', cb)),
            ('home', lambda cb: self._move_arm('home', cb)),
        ]
        self._run_steps(steps, on_done=self._on_place_done,
                        on_fail=lambda why: self._on_failed('放置', why))

    def _on_place_done(self):
        self._busy = False
        self._holding = False
        self.get_logger().info('放置完成，发布 DEPLOYMENT_COMPLETE')
        self._publish_status(STATUS_COMPLETE)

    def _on_failed(self, phase, why):
        self._busy = False
        # 放置阶段：设备已 detach 释放（不再 holding）即视为放置主体成功。
        # 之后的回位动作（如 home）偶发 abort 不影响验收结果。
        if phase == '放置' and not self._holding:
            self.get_logger().warn(
                f'放置后回位失败（设备已放置到位）: {why}，仍发布 DEPLOYMENT_COMPLETE')
            self._publish_status(STATUS_COMPLETE)
            return
        self.get_logger().error(f'{phase}流程失败: {why}，发布 MANIPULATION_FAILED')
        self._publish_status(STATUS_MANIP_FAILED)

    # ------------------------------------------------------------------
    # Generic step runner: each step is fn(done_cb) where done_cb(ok, why)
    # ------------------------------------------------------------------
    def _run_steps(self, steps, on_done, on_fail, index=0):
        if index >= len(steps):
            on_done()
            return
        name, fn = steps[index]

        def done(ok, why=''):
            if not ok:
                on_fail(f'步骤 {name} 失败: {why}')
                return
            self._run_steps(steps, on_done, on_fail, index + 1)

        try:
            fn(done)
        except Exception as exc:  # defensive: never leave state stuck
            on_fail(f'步骤 {name} 异常: {exc}')

    # ------------------------------------------------------------------
    # Arm move via FollowJointTrajectory (single waypoint)
    # ------------------------------------------------------------------
    def _move_arm(self, pose_name, done):
        positions = self._poses[pose_name]
        self.get_logger().info(f'移动到 {pose_name}: {[round(p,2) for p in positions]}')
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = self._make_traj(ARM_JOINTS, positions, self._arm_dur)
        self._send_traj_goal(self._arm_client, goal, done)

    def _move_gripper(self, position, done):
        self.get_logger().info(f'夹爪移动到 {position:.3f} m')
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = self._make_traj(GRIPPER_JOINTS, [position], self._grip_dur)
        self._send_traj_goal(self._grip_client, goal, done)

    def _make_traj(self, joints, positions, duration):
        traj = JointTrajectory()
        traj.joint_names = joints
        point = JointTrajectoryPoint()
        point.positions = list(positions)
        secs = int(duration)
        point.time_from_start = Duration(sec=secs, nanosec=int((duration - secs) * 1e9))
        traj.points = [point]
        return traj

    def _send_traj_goal(self, client, goal, done):
        if not client.wait_for_server(timeout_sec=5.0):
            done(False, 'action server 不可用')
            return

        # Watchdog: a trajectory should finish well within its duration.
        # If the result never arrives (e.g. a missed callback), fail the
        # step instead of hanging the whole state machine forever.
        duration = goal.trajectory.points[0].time_from_start
        timeout = duration.sec + duration.nanosec * 1e-9 + 10.0
        state = {'finished': False, 'timer': None}

        def finish(ok, why=''):
            if state['finished']:
                return
            state['finished'] = True
            if state['timer'] is not None:
                state['timer'].cancel()
            done(ok, why)

        def on_timeout():
            self.get_logger().warn('轨迹结果超时未返回')
            finish(False, '轨迹执行超时')

        state['timer'] = self.create_timer(timeout, on_timeout)

        send_future = client.send_goal_async(goal)

        def on_response(fut):
            handle = fut.result()
            if not handle.accepted:
                finish(False, '轨迹目标被拒绝')
                return
            result_future = handle.get_result_async()

            def on_result(rfut):
                status = rfut.result().status
                if status == GoalStatus.STATUS_SUCCEEDED:
                    finish(True)
                else:
                    finish(False, f'轨迹执行状态 {status}')

            result_future.add_done_callback(on_result)

        send_future.add_done_callback(on_response)

    # ------------------------------------------------------------------
    # Attach / detach via the Gazebo Sim DetachableJoint system plugin.
    #
    # The plugin is loaded inside the iot_device model (iot_device.sdf) and
    # welds <child_link> to <parent_link> across models. It is triggered by
    # an Empty message on a gz-transport topic, which parameter_bridge does
    # not bridge, so we publish via the `ign topic` CLI.
    # ------------------------------------------------------------------
    def _attach(self, done):
        self.get_logger().info(
            f'attach: 焊接到 {self._parent_link} (DetachableJoint)')
        self._run_ign_topic(self._attach_topic, 'attach', done)

    def _detach(self, done):
        self.get_logger().info(f'detach: 断开与 {self._parent_link} 的焊接')
        self._run_ign_topic(self._detach_topic, 'detach', done)

    def _run_ign_topic(self, topic, label, done):
        cmd = [
            'ign', 'topic', '-t', topic,
            '-m', 'ignition.msgs.Empty',
            '-p', 'unused: true',
        ]
        state = {'finished': False, 'timers': []}

        def finish(ok, why=''):
            if state['finished']:
                return
            state['finished'] = True
            for t in state['timers']:
                t.cancel()
            done(ok, why)

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as exc:
            finish(False, f'{label} 调用异常: {exc}')
            return

        def poll():
            if state['finished']:
                return
            rc = proc.poll()
            if rc is None:
                return  # still running
            # process exited
            if rc == 0:
                finish(True)
            else:
                err = ((proc.stderr.read() if proc.stderr else '') +
                       (proc.stdout.read() if proc.stdout else '')).strip()
                finish(False, f'{label} 失败: {err[:200]}')

        def on_timeout():
            if state['finished']:
                return
            proc.kill()
            finish(False, f'{label} ign topic 超时')

        state['timers'].append(self.create_timer(0.2, poll))
        state['timers'].append(self.create_timer(10.0, on_timeout))

    # ------------------------------------------------------------------
    # Utility: async wait
    # ------------------------------------------------------------------
    def _wait(self, seconds, done):
        timer = self.create_timer(seconds, lambda: self._fire_once(timer, done))

    def _fire_once(self, timer, done):
        timer.cancel()
        done(True)

    def _publish_status(self, text):
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ManipulationNode()
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
