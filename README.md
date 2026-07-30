# 🚁 UAV Swarm — AI-Powered Cooperative Drone Swarm for Autonomous Area Coverage & Object Detection

> **Final Year Project (FYP)**  
> Building a cooperative multi-UAV system that can autonomously cover an area, detect objects in real time, and execute safe waypoint missions using ROS 2 + ArduPilot SITL.

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble%2FJazzy-blue)](https://docs.ros.org/)
[![ArduPilot](https://img.shields.io/badge/ArduPilot-SITL-green)](https://ardupilot.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-red)](https://github.com/ultralytics/ultralytics)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-orange)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📌 Project Overview

This repository documents the complete development of an **AI-powered cooperative UAV swarm** capable of:

- Autonomous area coverage
- Real-time object detection (YOLOv8)
- Coordinated multi-drone missions
- Safe flight with battery & communication failsafes
- Full simulation pipeline (ArduPilot SITL + MAVROS + ROS 2)

The project is structured as a progressive weekly development log, starting from computer-vision fundamentals and evolving into a complete ROS 2 autonomous mission stack.

---

## 🏗️ Repository Structure

```text
UAV_SWARM/
├── src/
│   ├── drone_mission/          # Full ROS 2 autonomous waypoint mission package
│   │   ├── drone_mission/
│   │   │   ├── telemetry_monitor.py
│   │   │   ├── flight_controller.py
│   │   │   └── mission_controller.py   # State machine + failsafes
│   │   ├── launch/
│   │   ├── config/
│   │   └── README.md
│   └── my_robot_controller/    # Early ROS 2 learning nodes
│
├── uav week1/                  # Computer Vision & YOLO fundamentals
│   ├── Week1_opencv_numpy/
│   └── Week1_yolo/
│
├── uav week2/                  # Advanced detection & image processing
│   ├── Week_2_Yolo_Pascal/
│   ├── Sobel_Test/
│   ├── RGB material/
│   └── grayscale material/
│
├── uav week3/                  # Dataset engineering & motion detection
│   ├── Annotation_Conversion_YOLO/
│   ├── Annotation_Viulization/
│   ├── DataSet_Splitting/
│   ├── Motion_Detection_Frame_Difference/
│   └── YOLOv8 models (.pt)
│
└── log.txt


🚀 Progress Timeline
Week 1 — Foundations

TaskDescriptionStatusOpenCV + NumPyImage manipulation, array operations, basic computer vision pipeline✅ CompletedYOLOv8 Chicken DetectionFirst end-to-end object detection notebook using Ultralytics YOLOv8✅ Completed
Week 2 — Detection & Image Processing

TaskDescriptionStatusYOLO on Pascal VOCTraining / inference on Pascal VOC dataset✅ CompletedSobel OperatorEdge detection experiments✅ CompletedRGB & Grayscale PipelinesColor space handling and preprocessing✅ CompletedVideo ProcessingWorking with video streams and frame extraction✅ Completed
Week 3 — Dataset Engineering & Motion

TaskDescriptionStatusAnnotation ConversionPascal / VisDrone → YOLO format conversion✅ CompletedAnnotation VisualizationDrawing and verifying bounding boxes✅ CompletedDataset SplittingTrain / Val / Test split utilities✅ CompletedMotion DetectionFrame-difference based motion detection✅ CompletedYOLOv8 Modelsyolov8n.pt & yolov8s.pt integrated✅ Completed
Current Focus — ROS 2 Autonomous Flight

ComponentDescriptionStatusmy_robot_controllerBasic publisher / subscriber nodes✅ Completeddrone_mission packageFull autonomous waypoint mission with MAVROS + ArduPilot SITL✅ CompletedMission State MachineINIT → ARM → TAKEOFF → NAVIGATE ↔ HOVER → RTL → LAND → COMPLETE✅ CompletedFailsafesBattery %, connection timeout, FCU disconnect → automatic RTL✅ CompletedVisualizationLive RViz2 path + pose✅ CompletedRecordingROS 2 bag recording script✅ Completed

🛠️ Tech Stack

CategoryTechnologiesSimulationArduPilot SITL, Gazebo (optional)MiddlewareROS 2 (Humble / Jazzy), MAVROSFlight ControlArduCopter, GUIDED mode, RTLComputer VisionOpenCV, NumPy, Ultralytics YOLOv8LanguagesPython 3.10+ToolsRViz2, ros2 bag, Jupyter Notebooks

🛫 Running the Autonomous Mission
1. Prerequisites

Ubuntu 22.04 / 24.04
ROS 2 (Humble or Jazzy)
ArduPilot SITL
MAVROS

2. Build the package
Bashcd ~/mission_ws
colcon build --packages-select drone_mission
source install/setup.bash
3. Start ArduPilot SITL
Bashcd ~/ardupilot/ArduCopter
sim_vehicle.py -v ArduCopter --map --console
4. Launch the full mission
Bashros2 launch drone_mission mission.launch.py
Useful overrides:
Bashros2 launch drone_mission mission.launch.py \
  takeoff_altitude:=15.0 \
  hover_duration:=8.0 \
  battery_failsafe_pct:=25.0
5. Visualize in RViz2
Bashrviz2 -d install/drone_mission/share/drone_mission/config/mission.rviz
6. Record the mission
Bash./src/drone_mission/record_mission_bag.sh

🧠 Mission State Machine
textINIT
  ↓
ARMING / GUIDED
  ↓
TAKEOFF
  ↓
NAVIGATE ⇄ HOVER   (for every waypoint)
  ↓
RETURN_TO_LAUNCH
  ↓
LANDING
  ↓
MISSION_COMPLETE
Failsafe triggers (any time during NAVIGATE / HOVER):

Battery ≤ threshold
No MAVROS heartbeat for connection_timeout seconds
FCU reported as disconnected

→ Automatic switch to ArduPilot RTL mode.

👥 Team

MemberGitHubContributionsAhmad@oye-ahmadProject lead, ROS 2 mission stack, integrationZainab@zainababbasi5Computer vision, YOLO experiments, video pipelinesMuhammad Ahmad@Muhammad-AHMAD07Dataset tools, annotation conversion, Sobel / grayscaleMahnoor@sagittariusNoorEarly repository setup & contributions

📈 Future Roadmap

 Multi-UAV coordination & formation control
 Real-time object detection on live drone camera stream
 Cooperative area coverage algorithms (lawnmower, spiral, adaptive)
 Inter-drone communication (ROS 2 DDS / custom messaging)
 Hardware-in-the-loop (HITL) testing
 Real flight tests with PX4 / ArduPilot hardware


📄 License
This project is released under the MIT License. See LICENSE for details.

🙏 Acknowledgements

ArduPilot
ROS 2
Ultralytics YOLOv8
MAVROS
VisDrone & Pascal VOC datasets



Built with ❤️ by the UAV Swarm Team
Towards fully autonomous cooperative aerial systems

```
