import rclpy
from rclpy.node import Node

from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from rclpy.qos import HistoryPolicy

from mavros_msgs.msg import State
from sensor_msgs.msg import BatteryState, Imu, NavSatFix
from geometry_msgs.msg import PoseStamped


class TelemetryMonitor(Node):

    def __init__(self):
        super().__init__('telemetry_monitor')

        # MAVROS uses BEST_EFFORT QoS
        mavros_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST
        )

        # UAV State
        self.state_sub = self.create_subscription(
            State, '/mavros/state', self.state_callback, mavros_qos)

        # GPS Position
        self.gps_sub = self.create_subscription(
            NavSatFix, '/mavros/global_position/global', self.gps_callback, mavros_qos)

        # Local Position
        self.pose_sub = self.create_subscription(
            PoseStamped, '/mavros/local_position/pose', self.pose_callback, mavros_qos)

        # IMU Data
        self.imu_sub = self.create_subscription(
            Imu, '/mavros/imu/data', self.imu_callback, mavros_qos)

        # Battery
        self.battery_sub = self.create_subscription(
            BatteryState, '/mavros/battery', self.battery_callback, mavros_qos)

        self.connected = False
        self.mode = ""

        self.get_logger().info("Telemetry Monitor Started")

    def state_callback(self, msg):
        self.connected = msg.connected
        self.mode = msg.mode
        self.get_logger().info(
            f"FCU Connected: {msg.connected} | Mode: {msg.mode} | Armed: {msg.armed}")

    def gps_callback(self, msg):
        self.get_logger().info(
            f"GPS -> Lat: {msg.latitude:.6f}, Lon: {msg.longitude:.6f}, Alt: {msg.altitude:.2f} m")

    def pose_callback(self, msg):
        x = msg.pose.position.x
        y = msg.pose.position.y
        z = msg.pose.position.z
        self.get_logger().info(f"Position -> X:{x:.2f} Y:{y:.2f} Z:{z:.2f}")

    def imu_callback(self, msg):
        ax = msg.linear_acceleration.x
        ay = msg.linear_acceleration.y
        az = msg.linear_acceleration.z
        self.get_logger().info(f"IMU -> Ax:{ax:.2f} Ay:{ay:.2f} Az:{az:.2f}")

    def battery_callback(self, msg):
        if msg.percentage >= 0:
            percentage = msg.percentage * 100
            self.get_logger().info(f"Battery -> {percentage:.1f}% Voltage:{msg.voltage:.2f}V")
        else:
            self.get_logger().info(f"Battery -> Voltage:{msg.voltage:.2f}V")


def main(args=None):
    rclpy.init(args=args)
    node = TelemetryMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
