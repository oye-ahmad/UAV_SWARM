#!/usr/bin/env python3
"""
Boustrophedon (lawnmower) coverage path planner.

Subscribes once to a static /map (nav_msgs/OccupancyGrid), sweeps it in
horizontal rows spaced by `row_spacing_m`, alternating direction each row
(left->right, then right->left, etc.), skipping occupied cells.

Publishes the ordered waypoints as a nav_msgs/Path (local frame, matches
the map's frame_id) and writes them to a plain-text waypoint file
(lat/lon-free, local x/y in meters) for the MAVSDK executor to consume
later, after a local->global conversion using the drone's home position.
"""

import csv
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile
from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped


FREE = 0
OCCUPIED = 100
UNKNOWN = -1


class CoveragePlannerNode(Node):
    def __init__(self):
        super().__init__('coverage_planner_node')

        self.declare_parameter('row_spacing_m', 2.0)
        self.declare_parameter('inflate_cells', 1)  # shrink free space by N cells from obstacles
        self.declare_parameter('output_path_topic', '/coverage_path')
        self.declare_parameter('waypoint_file', os.path.expanduser('~/coverage_map/waypoints.csv'))

        self.row_spacing_m = self.get_parameter('row_spacing_m').value
        self.inflate_cells = self.get_parameter('inflate_cells').value
        self.waypoint_file = self.get_parameter('waypoint_file').value

        # /map from map_server is published latched (transient local) - match that QoS or we'll miss it
        map_qos = QoSProfile(depth=1)
        map_qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL

        self._map_received = False
        self._last_path = None
        self.create_subscription(OccupancyGrid, '/map', self.map_callback, map_qos)

        topic = self.get_parameter('output_path_topic').value
        self.path_pub = self.create_publisher(Path, topic, map_qos)

        # Belt-and-suspenders: also republish periodically. TRANSIENT_LOCAL should
        # deliver the last message to late subscribers on its own, but a periodic
        # republish means it works even if a viewer (e.g. RViz2) has a mismatched
        # or default (volatile) QoS override on its subscription.
        self.create_timer(2.0, self.republish_path)

        self.get_logger().info(
            f'Coverage planner up. row_spacing_m={self.row_spacing_m}, '
            f'waiting for /map...'
        )

    def map_callback(self, msg: OccupancyGrid):
        if self._map_received:
            return  # map is static for this mission, only plan once
        self._map_received = True
        self.get_logger().info(
            f'Got map: {msg.info.width}x{msg.info.height} @ {msg.info.resolution} m/cell'
        )

        waypoints_local = self.plan_boustrophedon(msg)
        self.get_logger().info(f'Planned {len(waypoints_local)} waypoints.')

        self.publish_path(waypoints_local, msg.header.frame_id)
        self.write_waypoint_file(waypoints_local)

        self.get_logger().info(f'Waypoints written to {self.waypoint_file}')

    def plan_boustrophedon(self, msg: OccupancyGrid):
        w, h = msg.info.width, msg.info.height
        res = msg.info.resolution
        ox, oy = msg.info.origin.position.x, msg.info.origin.position.y
        data = msg.data  # flat, row-major, row 0 = bottom of map per REP-103/nav_msgs convention

        grid = [[data[row * w + col] for col in range(w)] for row in range(h)]

        # Optional safety margin: treat any free cell within `inflate_cells` of an
        # occupied cell as occupied too, so the drone doesn't clip the border.
        if self.inflate_cells > 0:
            grid = self.inflate_obstacles(grid, w, h, self.inflate_cells)

        row_spacing_cells = max(1, round(self.row_spacing_m / res))

        waypoints = []  # list of (x, y) in local meters
        left_to_right = True

        for row in range(0, h, row_spacing_cells):
            cols = range(w) if left_to_right else range(w - 1, -1, -1)
            row_points = []
            for col in cols:
                if grid[row][col] == FREE:
                    x = ox + (col + 0.5) * res
                    y = oy + (row + 0.5) * res
                    row_points.append((x, y))
            if row_points:
                # collapse a run of free cells in a row down to its endpoints -
                # no need for a waypoint at every single grid cell
                waypoints.append(row_points[0])
                if row_points[-1] != row_points[0]:
                    waypoints.append(row_points[-1])
                left_to_right = not left_to_right

        return waypoints

    @staticmethod
    def inflate_obstacles(grid, w, h, n):
        occupied = set()
        for row in range(h):
            for col in range(w):
                if grid[row][col] != FREE:
                    occupied.add((row, col))

        inflated = {p for p in occupied}
        for row, col in occupied:
            for dr in range(-n, n + 1):
                for dc in range(-n, n + 1):
                    r, c = row + dr, col + dc
                    if 0 <= r < h and 0 <= c < w:
                        inflated.add((r, c))

        new_grid = [row[:] for row in grid]
        for row, col in inflated:
            new_grid[row][col] = OCCUPIED
        return new_grid

    def publish_path(self, waypoints_local, frame_id):
        path = Path()
        path.header.frame_id = frame_id
        path.header.stamp = self.get_clock().now().to_msg()
        for x, y in waypoints_local:
            pose = PoseStamped()
            pose.header = path.header
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.orientation.w = 1.0
            path.poses.append(pose)
        self._last_path = path
        self.path_pub.publish(path)

    def republish_path(self):
        if self._last_path is not None:
            self._last_path.header.stamp = self.get_clock().now().to_msg()
            self.path_pub.publish(self._last_path)

    def write_waypoint_file(self, waypoints_local):
        os.makedirs(os.path.dirname(self.waypoint_file), exist_ok=True)
        with open(self.waypoint_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['seq', 'x_local_m', 'y_local_m'])
            for i, (x, y) in enumerate(waypoints_local):
                writer.writerow([i, f'{x:.3f}', f'{y:.3f}'])


def main(args=None):
    rclpy.init(args=args)
    node = CoveragePlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
