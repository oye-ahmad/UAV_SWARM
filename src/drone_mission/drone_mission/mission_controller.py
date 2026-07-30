import math
import time
import signal
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from mavros_msgs.msg import State
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav_msgs.msg import Path


class MissionState(Enum):
    INIT = auto()
    ARMING = auto()
    TAKEOFF = auto()
    NAVIGATE = auto()
    HOVER = auto()
    RETURN_TO_LAUNCH = auto()
    LANDING = auto()
    MISSION_COMPLETE = auto()
    FAILSAFE = auto()


class MissionController(Node):
    """
    Autonomous waypoint mission controller for ArduPilot SITL via MAVROS2.

    Sequence: ARM -> GUIDED -> TAKEOFF -> waypoint navigation (velocity
    commands, closed loop on local position) -> hover at each waypoint ->
    RTL -> LAND. Continuously monitors battery and FCU connection and will
    override the mission with an RTL failsafe if thresholds are breached.
    """

    def __init__(self):
        super().__init__('mission_controller')

        # ---------------- Parameters ----------------
        self.declare_parameter('takeoff_altitude', 10.0)
        self.declare_parameter('hover_duration', 5.0)          # seconds per waypoint
        self.declare_parameter('waypoint_tolerance', 0.5)      # metres
        self.declare_parameter('max_horizontal_speed', 2.0)    # m/s
        self.declare_parameter('max_vertical_speed', 1.0)      # m/s
        self.declare_parameter('battery_failsafe_pct', 20.0)   # percent
        # /mavros/state is only published on each heartbeat (~1Hz from
        # ArduPilot, sometimes slower under SITL load), so this needs
        # meaningful slack above that rate or it false-triggers.
        self.declare_parameter('connection_timeout', 10.0)     # seconds
        self.declare_parameter('request_retry_interval', 1.0)  # seconds
        self.declare_parameter('control_rate_hz', 20.0)
        # Waypoints are in the local ENU frame relative to the arming
        # position (x=East, y=North, z=Up), in metres.
        self.declare_parameter(
            'waypoints_x', [10.0, 10.0, 0.0]
        )
        self.declare_parameter(
            'waypoints_y', [0.0, 10.0, 10.0]
        )
        self.declare_parameter(
            'waypoints_z', [10.0, 10.0, 10.0]
        )

        self.takeoff_altitude = self.get_parameter('takeoff_altitude').value
        self.hover_duration = self.get_parameter('hover_duration').value
        self.wp_tolerance = self.get_parameter('waypoint_tolerance').value
        self.max_h_speed = self.get_parameter('max_horizontal_speed').value
        self.max_v_speed = self.get_parameter('max_vertical_speed').value
        self.battery_failsafe_pct = self.get_parameter('battery_failsafe_pct').value
        self.connection_timeout = self.get_parameter('connection_timeout').value
        self.request_retry_interval = self.get_parameter('request_retry_interval').value
        control_rate = self.get_parameter('control_rate_hz').value

        wx = self.get_parameter('waypoints_x').value
        wy = self.get_parameter('waypoints_y').value
        wz = self.get_parameter('waypoints_z').value
        self.waypoints = list(zip(wx, wy, wz))

        # ---------------- QoS (MAVROS uses BEST_EFFORT) ----------------
        mavros_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )

        # ---------------- Subscriptions ----------------
        self.state_sub = self.create_subscription(
            State, '/mavros/state', self.state_cb, mavros_qos)
        self.pose_sub = self.create_subscription(
            PoseStamped, '/mavros/local_position/pose', self.pose_cb, mavros_qos)
        self.battery_sub = self.create_subscription(
            BatteryState, '/mavros/battery', self.battery_cb, mavros_qos)

        # ---------------- Publishers ----------------
        self.vel_pub = self.create_publisher(
            TwistStamped, '/mavros/setpoint_velocity/cmd_vel', 10)
        self.path_pub = self.create_publisher(Path, '/mission/flight_path', 10)
        self.flight_path = Path()

        # ---------------- Service clients ----------------
        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.land_client = self.create_client(CommandTOL, '/mavros/cmd/land')

        for client, name in (
            (self.arm_client, 'arming'),
            (self.mode_client, 'set_mode'),
            (self.takeoff_client, 'takeoff'),
            (self.land_client, 'land'),
        ):
            while not client.wait_for_service(timeout_sec=1.0):
                self.get_logger().info(f'Waiting for /mavros/cmd/{name} service...')

        # ---------------- Internal state ----------------
        self.connected = False
        self.armed = False
        self.mode = ""
        self.last_state_time = self.get_clock().now()

        self.current_pose = None
        self.home_position = None  # captured once local position is first received

        self.battery_pct = 100.0
        self.battery_received = False

        self.state = MissionState.INIT
        self.current_wp_index = 0
        self.hover_start_time = None
        self.pre_failsafe_state = None
        self.mission_started_logged = False

        # Guards against re-issuing an async service request every control
        # tick while a previous one is still in flight.
        self.mode_request_pending = False
        self.arm_request_pending = False
        self.rtl_sent = False
        # Rate-limit retries so we don't flood MAVROS while waiting for the
        # (slower) /mavros/state topic to confirm a request took effect.
        self.last_mode_attempt_time = 0.0
        self.last_arm_attempt_time = 0.0

        # Set by the SIGINT handler in main() — checked each control tick so
        # the abort is handled by the normal running state machine rather
        # than by code that runs after spin() has already returned (by then
        # rclpy's own SIGINT handler has usually already invalidated the
        # context, so publishing/service calls from there fail outright).
        self.abort_requested = False
        self.shutdown_ready = False

        self.control_timer = self.create_timer(
            1.0 / control_rate, self.control_loop)

        self.get_logger().info(
            f'Mission Controller started with {len(self.waypoints)} waypoints.')

    # ==================================================================
    # Callbacks
    # ==================================================================
    def state_cb(self, msg: State):
        self.connected = msg.connected
        self.armed = msg.armed
        self.mode = msg.mode
        self.last_state_time = self.get_clock().now()

    def pose_cb(self, msg: PoseStamped):
        self.current_pose = msg
        if self.home_position is None:
            self.home_position = (
                msg.pose.position.x,
                msg.pose.position.y,
                msg.pose.position.z,
            )
            self.get_logger().info(f'Home position captured: {self.home_position}')

        # Accumulate and republish the flown path for RViz2 visualization
        self.flight_path.header = msg.header
        self.flight_path.header.frame_id = 'map'
        self.flight_path.poses.append(msg)
        self.path_pub.publish(self.flight_path)

    def battery_cb(self, msg: BatteryState):
        if msg.percentage >= 0:
            self.battery_pct = msg.percentage * 100.0
            self.battery_received = True

    # ==================================================================
    # Service helpers (non-blocking — safe to call from a timer callback)
    # ==================================================================
    # IMPORTANT: never use rclpy.spin_until_future_complete() from inside a
    # timer/subscription callback. control_loop() runs *inside* rclpy.spin(),
    # so a nested blocking spin on the same node deadlocks silently (this is
    # exactly what caused the earlier hang after "Setting GUIDED mode and
    # arming..."). Use call_async() + add_done_callback() instead, and let
    # the outer spin() deliver the response on its own.

    def call_set_mode_async(self, mode: str, on_done=None):
        req = SetMode.Request()
        req.custom_mode = mode
        future = self.mode_client.call_async(req)

        def _cb(fut):
            try:
                result = fut.result()
            except Exception as e:
                self.get_logger().error(f'set_mode service call failed: {e}')
                if on_done:
                    on_done(False)
                return
            if result.mode_sent:
                self.get_logger().info(f'Mode change requested: {mode}')
            else:
                self.get_logger().error(f'Mode change rejected: {mode}')
            if on_done:
                on_done(bool(result.mode_sent))

        future.add_done_callback(_cb)

    def call_arm_async(self, value: bool, on_done=None):
        req = CommandBool.Request()
        req.value = value
        future = self.arm_client.call_async(req)

        def _cb(fut):
            try:
                result = fut.result()
            except Exception as e:
                self.get_logger().error(f'arming service call failed: {e}')
                if on_done:
                    on_done(False)
                return
            if result.success:
                self.get_logger().info(f'Arm request success (value={value})')
            else:
                self.get_logger().error('Arm request rejected')
            if on_done:
                on_done(bool(result.success))

        future.add_done_callback(_cb)

    def call_takeoff_async(self, altitude: float, on_done=None):
        req = CommandTOL.Request()
        req.altitude = altitude
        future = self.takeoff_client.call_async(req)

        def _cb(fut):
            try:
                result = fut.result()
            except Exception as e:
                self.get_logger().error(f'takeoff service call failed: {e}')
                if on_done:
                    on_done(False)
                return
            if result.success:
                self.get_logger().info(f'Takeoff command accepted: {altitude}m')
            else:
                self.get_logger().error('Takeoff command rejected')
            if on_done:
                on_done(bool(result.success))

        future.add_done_callback(_cb)

    def call_land_async(self, on_done=None):
        req = CommandTOL.Request()
        req.altitude = 0.0
        future = self.land_client.call_async(req)

        def _cb(fut):
            try:
                result = fut.result()
            except Exception as e:
                self.get_logger().error(f'land service call failed: {e}')
                if on_done:
                    on_done(False)
                return
            if result.success:
                self.get_logger().info('Land command accepted')
            else:
                self.get_logger().error('Land command rejected')
            if on_done:
                on_done(bool(result.success))

        future.add_done_callback(_cb)

    # ==================================================================
    # Failsafe checks
    # ==================================================================
    def failsafe_triggered(self) -> bool:
        if self.state in (MissionState.FAILSAFE, MissionState.RETURN_TO_LAUNCH,
                           MissionState.LANDING, MissionState.MISSION_COMPLETE,
                           MissionState.INIT, MissionState.ARMING):
            return False

        if self.battery_received and self.battery_pct <= self.battery_failsafe_pct:
            self.get_logger().warn(
                f'FAILSAFE: battery at {self.battery_pct:.1f}% '
                f'<= threshold {self.battery_failsafe_pct}%')
            return True

        elapsed = (self.get_clock().now() - self.last_state_time).nanoseconds / 1e9
        if elapsed > self.connection_timeout:
            self.get_logger().warn(
                f'FAILSAFE: no /mavros/state update for {elapsed:.1f}s')
            return True

        if not self.connected:
            self.get_logger().warn('FAILSAFE: FCU reports disconnected')
            return True

        return False

    # ==================================================================
    # Velocity control helper
    # ==================================================================
    def publish_velocity_towards(self, target_x, target_y, target_z):
        cur = self.current_pose.pose.position
        dx = target_x - cur.x
        dy = target_y - cur.y
        dz = target_z - cur.z

        horiz_dist = math.sqrt(dx * dx + dy * dy)

        # Simple proportional controller, clamped to max speed
        kp = 0.6
        vx = max(-self.max_h_speed, min(self.max_h_speed, kp * dx))
        vy = max(-self.max_h_speed, min(self.max_h_speed, kp * dy))
        vz = max(-self.max_v_speed, min(self.max_v_speed, kp * dz))

        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.twist.linear.x = vx
        msg.twist.linear.y = vy
        msg.twist.linear.z = vz
        self.vel_pub.publish(msg)

        return horiz_dist, abs(dz)

    def publish_zero_velocity(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        self.vel_pub.publish(msg)

    # ==================================================================
    # Main control loop / state machine
    # ==================================================================
    def control_loop(self):
        # Wait until we have a first local position fix before doing anything
        if self.current_pose is None:
            return

        # Check failsafe conditions before evaluating the mission state
        if self.failsafe_triggered():
            self.pre_failsafe_state = self.state
            self.state = MissionState.FAILSAFE

        # A Ctrl+C abort request is handled the same way as any other
        # failsafe: hand off to RTL and let ArduPilot bring it home safely
        # rather than just killing the process mid-flight.
        if self.abort_requested and self.state not in (
                MissionState.FAILSAFE, MissionState.RETURN_TO_LAUNCH,
                MissionState.LANDING, MissionState.MISSION_COMPLETE):
            self.get_logger().warn('Abort requested — commanding RTL instead of exiting mid-flight')
            self.pre_failsafe_state = self.state
            self.state = MissionState.FAILSAFE

        if self.state == MissionState.INIT:
            # Drive off the real FCU state (self.mode / self.armed, updated
            # by state_cb from /mavros/state) rather than a local flag, so
            # the request is naturally retried until MAVROS confirms it.
            # Retries are rate-limited to request_retry_interval since
            # /mavros/state only updates on each heartbeat (~1Hz) — without
            # this, every 20Hz control tick re-fires the service call,
            # flooding the executor and starving the state subscription.
            now = time.time()
            if self.mode != 'GUIDED':
                if (not self.mode_request_pending and
                        now - self.last_mode_attempt_time > self.request_retry_interval):
                    self.get_logger().info('Requesting GUIDED mode...')
                    self.mode_request_pending = True
                    self.last_mode_attempt_time = now
                    self.call_set_mode_async(
                        'GUIDED',
                        on_done=lambda ok: setattr(self, 'mode_request_pending', False))
            elif not self.armed:
                if (not self.arm_request_pending and
                        now - self.last_arm_attempt_time > self.request_retry_interval):
                    self.get_logger().info('Requesting arm...')
                    self.arm_request_pending = True
                    self.last_arm_attempt_time = now
                    self.call_arm_async(
                        True,
                        on_done=lambda ok: setattr(self, 'arm_request_pending', False))
            else:
                self.get_logger().info('GUIDED + armed confirmed. Proceeding to takeoff.')
                self.state = MissionState.TAKEOFF

        elif self.state == MissionState.TAKEOFF:
            if not self.mission_started_logged:
                self.call_takeoff_async(self.takeoff_altitude)
                self.mission_started_logged = True
            target_alt = self.home_position[2] + self.takeoff_altitude
            if abs(self.current_pose.pose.position.z - target_alt) < self.wp_tolerance:
                self.get_logger().info('Takeoff altitude reached. Beginning waypoint navigation.')
                self.current_wp_index = 0
                self.state = MissionState.NAVIGATE

        elif self.state == MissionState.NAVIGATE:
            wx, wy, wz = self.waypoints[self.current_wp_index]
            # waypoints are relative to home in ENU
            tx = self.home_position[0] + wx
            ty = self.home_position[1] + wy
            tz = self.home_position[2] + wz
            horiz_dist, vert_dist = self.publish_velocity_towards(tx, ty, tz)
            if horiz_dist < self.wp_tolerance and vert_dist < self.wp_tolerance:
                self.get_logger().info(
                    f'Reached waypoint {self.current_wp_index + 1}/{len(self.waypoints)}')
                self.publish_zero_velocity()
                self.hover_start_time = time.time()
                self.state = MissionState.HOVER

        elif self.state == MissionState.HOVER:
            self.publish_zero_velocity()
            if time.time() - self.hover_start_time >= self.hover_duration:
                self.current_wp_index += 1
                if self.current_wp_index >= len(self.waypoints):
                    self.get_logger().info('All waypoints visited. Returning to launch.')
                    self.state = MissionState.RETURN_TO_LAUNCH
                else:
                    self.state = MissionState.NAVIGATE

        elif self.state == MissionState.RETURN_TO_LAUNCH:
            if not self.rtl_sent:
                self.call_set_mode_async('RTL')
                self.rtl_sent = True
            self.state = MissionState.LANDING

        elif self.state == MissionState.LANDING:
            # ArduPilot's RTL mode handles descent, land, and disarm on its
            # own; we just wait for disarm to confirm mission completion.
            if not self.armed:
                self.get_logger().info('UAV disarmed. Mission complete.')
                self.state = MissionState.MISSION_COMPLETE

        elif self.state == MissionState.FAILSAFE:
            if not self.rtl_sent:
                self.get_logger().warn('FAILSAFE ACTIVE: commanding RTL')
                self.call_set_mode_async('RTL')
                self.rtl_sent = True
            self.state = MissionState.LANDING

        elif self.state == MissionState.MISSION_COMPLETE:
            self.shutdown_ready = True


def main(args=None):
    rclpy.init(args=args)
    node = MissionController()

    # rclpy installs its own SIGINT handler that shuts the context down as
    # soon as Ctrl+C is pressed. If you try to do cleanup (publish, call a
    # service) inside a `except KeyboardInterrupt` block after spin()
    # returns, the context is usually already dead and every call fails
    # with "publisher's context is invalid" / similar. Instead, override
    # the handler to just set a flag, and let the still-running node
    # (spun manually below via spin_once) react to it through the normal
    # state machine — it already knows how to command RTL safely.
    press_count = {'n': 0}

    def sigint_handler(sig, frame):
        press_count['n'] += 1
        if press_count['n'] == 1:
            node.get_logger().warn(
                'Ctrl+C received — commanding RTL and waiting for landing. '
                'Press Ctrl+C again to force-exit immediately.')
            node.abort_requested = True
        else:
            node.get_logger().warn('Second Ctrl+C — forcing immediate exit.')
            node.shutdown_ready = True

    signal.signal(signal.SIGINT, sigint_handler)

    try:
        # Manual spin loop (instead of rclpy.spin()) so we can check
        # shutdown_ready between iterations without relying on an
        # exception-based exit path.
        while rclpy.ok() and not node.shutdown_ready:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()