from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package= 'my_robot_controller',
             executable='ahmad_node',
             name='Publisher',
             output='screen'),
        Node(package= 'my_robot_controller',
             executable='subscriber_node',
             name='Subscriber',
             output='screen')
    ])