#!/usr/bin/env python3

import rclpy

from rclpy.node import Node
from std_msgs.msg import String


class myNode(Node):
    def __init__(self):
        super().__init__("Publisher")

        self.publisher_ = self.create_publisher(String, 'hello_count', 10)
        timer=0.1
        self.create_timer(timer, self.timer_callback)
        self.counter=0

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