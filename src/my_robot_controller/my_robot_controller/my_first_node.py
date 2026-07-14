#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
from std_msgs.msg import String
from rcl_interfaces.msg import SetParametersResult


class myNode(Node):
    def __init__(self):
        super().__init__("Publisher")

        self.publisher_ = self.create_publisher(String, 'hello_count', 10)
        self.declare_parameter("timer", 0.1)
        timer=self.get_parameter("timer").value
        self.timer=self.create_timer(timer, self.timer_callback)
        self.counter=0

        self.add_on_set_parameters_callback(
            self.parameter_callback
        )


    def parameter_callback(self, params):

        for param in params:

            if param.name == "timer":

                self.get_logger().info(
                    f"Timer changed to {param.value}"
                )

                self.timer.cancel()

                self.timer = self.create_timer(
                    param.value,
                    self.timer_callback
                )

        return SetParametersResult(
            successful=True
        )

    def timer_callback(self):

        msg = String()

        msg.data = f"Hello {self.counter}"

        self.publisher_.publish(msg)

        self.get_logger().info(f"Publish: {msg.data}")
        self.counter+=1

    



def main(args=None):
    rclpy.init(args=args)

    node = myNode()

    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()