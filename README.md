# DronePad — Drone Control & Telemetry Desktop App

![Python](https://img.shields.io/badge/Python-3.11-3776ab?style=flat-square&logo=python)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-ff6b35?style=flat-square)
![MAVLink](https://img.shields.io/badge/Protocol-MAVLink2-00b4d8?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)

> Professional desktop application for drone flight control, real-time telemetry monitoring, and autonomous mission planning. Built with Python + Tkinter + MAVLink.

![DronePad Preview](./assets/preview.png)

## Features

- 🚩 **Real-time telemetry** — GPS, altitude, battery, attitude, speed updated at 10Hz
- 🗺️ **Interactive map view** — live drone position with heading indicator
- 📍 **Mission planner** — drag-and-drop waypoints, altitude per leg, loiter/land commands
- 🔋 **Battery & health dashboard** — cell voltage, current draw, estimated flight time remaining
- 📡 **MAVLink 2 over UDP/Serial** — compatible with ArduPilot, PX4, and any MAVLink-compliant FC
- 📄 **Flight log recorder** — auto-saves telemetry to CSV on arm, plays back any session
- ⚠️ **Alert system** — configurable thresholds for battery, signal, geofence breach
- 🌙 **Dark / light theme** — designed for outdoor readability

## Screenshots

| Telemetry Dashboard | Mission Planner | Flight Log |
|---|---|---|
| ![dash](./assets/dash.png) | ![mission](./assets/mission.png) | ![log](./assets/log.png) |

## Requirements

```
Python >= 3.10
pymavlink >= 2.4.37
pillow >= 10.0
matplotlib >= 3.8
pandas >= 2.0
```

## Installation

```bash
git clone https://github.com/semicolon-ai-dev/dronepad
cd dronepad
pip install -r requirements.txt
python main.py
```

## Connecting to a Drone

**UDP (Simulator / network):**
```
Connection string: udp:127.0.0.1:14550
```

**Serial (USB/radio):**
```
Connection string: /dev/ttyUSB0:57600
```

**Mission Planner / QGC bridge:**
Forward MAVLink traffic to `udp:localhost:14550`.

## Project Structure

```
dronepad/
├── main.py                # Entry point
├── app/
│   ├── ui/
│   │   ├── dashboard.py   # Main telemetry view
│   │   ├── map_view.py    # Interactive map canvas
│   │   ├── mission.py     # Waypoint mission editor
│   │   ├── log_viewer.py  # Flight log playback
│   │   └── alerts.py      # Alert configuration panel
│   ├── mavlink_handler.py # MAVLink connection & parsing
│   ├── telemetry.py       # Telemetry data model
│   ├── mission_planner.py # Mission logic & validation
│   └── logger.py          # CSV flight log writer
├── assets/
├── requirements.txt
└── README.md
```

## Built With AI Assistance

- **Claude Max** — MAVLink protocol integration & async architecture
- **Cursor Ultra** — Tkinter canvas rendering & widget layout
- **ChatGPT Pro** — mission validation logic & edge cases

**Build time: ~4 hours** including full MAVLink integration and SITL testing.

---

MIT License © 2026 [semicolon-ai-dev](https://github.com/semicolon-ai-dev)
