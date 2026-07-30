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


# 🚀 Progress Timeline

## Week 1 — Foundations

| Task | Description | Status |
|---|---|---|
| OpenCV + NumPy | Image manipulation, array operations, and basic computer vision pipeline | ✅ Completed |
| YOLOv8 Chicken Detection | First end-to-end object detection notebook using Ultralytics YOLOv8 | ✅ Completed |

---

# Week 2 — Detection & Image Processing

| Task | Description | Status |
|---|---|---|
| YOLO on Pascal VOC | Training and inference on Pascal VOC dataset | ✅ Completed |
| Sobel Operator | Edge detection experiments | ✅ Completed |
| RGB & Grayscale Pipelines | Color space handling and preprocessing | ✅ Completed |
| Video Processing | Working with video streams and frame extraction | ✅ Completed |

---

# Week 3 — Dataset Engineering & Motion

| Task | Description | Status |
|---|---|---|
| Annotation Conversion | Pascal VOC / VisDrone → YOLO format conversion | ✅ Completed |
| Annotation Visualization | Drawing and verifying bounding boxes | ✅ Completed |
| Dataset Splitting | Train / Validation / Test split utilities | ✅ Completed |
| Motion Detection | Frame-difference based motion detection | ✅ Completed |
| YOLOv8 Models | Integration of `yolov8n.pt` and `yolov8s.pt` models | ✅ Completed |

---

# Current Focus — ROS 2 Autonomous Flight

| Component | Description | Status |
|---|---|---|
| `my_robot_controller` | Basic ROS 2 publisher / subscriber nodes | ✅ Completed |
| `drone_mission` Package | Full autonomous waypoint mission with MAVROS + ArduPilot SITL | ✅ Completed |
| Mission State Machine | INIT → ARM → TAKEOFF → NAVIGATE ↔ HOVER → RTL → LAND → COMPLETE | ✅ Completed |
| Failsafes | Battery %, connection timeout, FCU disconnect → automatic RTL | ✅ Completed |
| Visualization | Live RViz2 path and UAV pose visualization | ✅ Completed |
| Recording | ROS 2 bag recording script | ✅ Completed |


---

# 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| Simulation | ArduPilot SITL, Gazebo (optional) |
| Middleware | ROS 2 (Humble / Jazzy), MAVROS |
| Flight Control | ArduCopter, GUIDED mode, RTL |
| Computer Vision | OpenCV, NumPy, Ultralytics YOLOv8 |
| Programming Language | Python 3.10+ |
| Development Tools | RViz2, ros2 bag, Jupyter Notebooks |

---

# 🛫 Running the Autonomous Mission

## 1. Prerequisites

Install the following:

- Ubuntu 22.04 / 24.04
- ROS 2 Humble or Jazzy
- ArduPilot SITL
- MAVROS


---

## 2. Build the ROS 2 Package

```bash
cd ~/mission_ws

colcon build --packages-select drone_mission

source install/setup.bash
