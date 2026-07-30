#!/bin/bash
# Records the full mission for later playback/analysis in RViz2 or rosbag2 tools.
# Usage: ./record_mission_bag.sh [output_name]

BAG_NAME=${1:-mission_$(date +%Y%m%d_%H%M%S)}

ros2 bag record -o "$BAG_NAME" \
  /mavros/state \
  /mavros/battery \
  /mavros/global_position/global \
  /mavros/local_position/pose \
  /mavros/imu/data \
  /mavros/setpoint_velocity/cmd_vel \
  /mission/flight_path \
  /tf \
  /tf_static
