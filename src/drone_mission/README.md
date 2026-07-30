# drone_mission — ROS2 + ArduPilot SITL Autonomous Waypoint Mission

## 1. Package layout
```
drone_mission/
├── drone_mission/
│   ├── telemetry_monitor.py    # your existing node (unchanged)
│   ├── flight_controller.py    # your existing node (+ land service added)
│   └── mission_controller.py   # new: waypoint mission + failsafe state machine
├── launch/mission.launch.py    # brings up MAVROS + all three nodes together
├── config/mission.rviz         # RViz2 layout for live pose + flight path
├── record_mission_bag.sh       # records a ros2 bag of the full mission
└── package.xml / setup.py
```

## 2. Build
```bash
cd ~/mission_ws
colcon build --packages-select drone_mission
source install/setup.bash
```

## 3. Start ArduPilot SITL
```bash
cd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter --map --console
```
This exposes MAVLink on `udp://127.0.0.1:14550` by default — matches the
`fcu_url` default in `mission.launch.py`. Adjust if your SITL setup differs.

## 4. Launch MAVROS + the mission
```bash
ros2 launch drone_mission mission.launch.py
```
Useful overrides:
```bash
ros2 launch drone_mission mission.launch.py \
  takeoff_altitude:=15.0 hover_duration:=8.0 battery_failsafe_pct:=25.0
```
Edit the `waypoints_x/y/z` parameters in `mission_controller.py` (or pass
them as launch params) to change the waypoint list — they're metres offset
from the arming position in the local ENU frame.

## 5. Visualize in RViz2
```bash
rviz2 -d install/drone_mission/share/drone_mission/config/mission.rviz
```
This shows the live UAV pose (`/mavros/local_position/pose`) and the
accumulated flight path (`/mission/flight_path`), published by
`mission_controller`.

## 6. Record the mission
In a separate terminal, before or right as you launch the mission:
```bash
cd ~/mission_ws
./src/drone_mission/record_mission_bag.sh
```
Stop with Ctrl+C once the UAV has landed and disarmed.

## 7. Analyze the recorded bag
```bash
ros2 bag info mission_<timestamp>       # summary: topics, message counts, duration
ros2 bag play mission_<timestamp>       # replay into RViz2 for a visual walkthrough
```
For plotting (e.g. battery drain, altitude profile over time), the
`data-analysis` workflow of extracting bag data to CSV/pandas and charting
(`rqt_plot`, or exporting via `ros2 bag` + `rosbag2_py` API) is worth using —
say the word and I can build that extraction script too, once you've got a
mission recorded.

## 8. Mission state machine (mission_controller.py)
```
INIT → ARMING/GUIDED → TAKEOFF → NAVIGATE ⇄ HOVER (per waypoint)
      → RETURN_TO_LAUNCH → LANDING → MISSION_COMPLETE
```
`FAILSAFE` can interrupt NAVIGATE/HOVER at any point if:
- battery percentage drops to/below `battery_failsafe_pct`, or
- no `/mavros/state` heartbeat is received for `connection_timeout` seconds, or
- MAVROS reports the FCU as disconnected

On trigger it commands ArduPilot's built-in `RTL` mode (which itself handles
the return, descent, land, and disarm), then the state machine waits for
disarm to confirm mission completion.
