import rclpy
from rclpy.node import Node

from mavros_msgs.srv import CommandBool
from mavros_msgs.srv import SetMode
from mavros_msgs.srv import CommandTOL


class FlightController(Node):

    def __init__(self):
        super().__init__('flight_controller')

        self.arm_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.land_client = self.create_client(CommandTOL, '/mavros/cmd/land')

        self.get_logger().info("Flight Controller Started")

        while not self.arm_client.wait_for_service(timeout_sec=1):
            self.get_logger().info("Waiting for MAVROS...")

    def arm(self):
        request = CommandBool.Request()
        request.value = True
        future = self.arm_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info("UAV Armed")
        else:
            self.get_logger().error("Arm Failed")

    def set_mode(self, mode):
        request = SetMode.Request()
        request.custom_mode = mode
        future = self.mode_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result().mode_sent:
            self.get_logger().info(f"Mode Changed: {mode}")

    def takeoff(self, altitude):
        request = CommandTOL.Request()
        request.altitude = altitude
        future = self.takeoff_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info(f"Takeoff {altitude}m")

    def land(self):
        request = CommandTOL.Request()
        request.altitude = 0.0
        future = self.land_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info("Landing")


def main(args=None):
    rclpy.init(args=args)
    node = FlightController()

    # TEST SEQUENCE
    node.set_mode("GUIDED")
    node.arm()
    node.takeoff(10.0)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
