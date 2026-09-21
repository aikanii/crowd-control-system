# Crowd Control System

### Real-time People Counting, Occupancy Monitoring & Crowd Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-000000?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-passing-brightgreen?style=flat-square)](/tests)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](/Dockerfile)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=flat-square)](https://github.com/psf/black)

> **v2.0 Rewrite** - Fully functional, production-ready crowd analytics system with multi-backend detection, threaded video pipeline, REST API, and real-time web dashboard. Fixed 9 critical bugs from v1.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [CLI](#cli)
  - [Python API](#python-api)
  - [REST API](#rest-api)
  - [Web Dashboard](#web-dashboard)
- [Detector Backends](#-detector-backends)
- [Development](#-development)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Changelog](#-changelog)
- [License](#-license)

---

## 🔍 Overview

Crowd Control System is an edge-ready computer vision platform for **real-time people counting and occupancy monitoring**. It processes live camera feeds (webcam, IP camera, video files) to:

1. **Detect** people using MobileNet SSD / HOG / YOLOv8
2. **Track** individuals across frames with centroid + correlation tracking
3. **Count** entries/exits via virtual counting line
4. **Monitor** occupancy and trigger alerts when thresholds are exceeded
5. **Visualize** via web dashboard with live feed, charts, and REST API

**Use cases:** Retail analytics, building occupancy compliance, event safety, smart offices, COVID capacity monitoring.

### Why v2.0?

Original v1 had critical runtime bugs (undefined variables, broken threading, incorrect counting logic, hard crashes on missing dependencies). v2.0 is a complete rewrite maintaining backward compatibility while adding production features.

---

## ✨ Features

| Category | Features |
|----------|----------|
| **Detection** | MobileNet SSD (Caffe), HOG (always available), YOLOv8 (optional), auto-fallback chain |
| **Tracking** | Centroid tracker + dlib correlation (optional), ID persistence, direction & speed estimation |
| **Counting** | Virtual line, bi-directional (Enter/Exit), occupancy = Enter - Exit, event history |
| **Alerts** | Email (SMTP with cooldown), Webhook (Slack/Discord/custom), Console fallback |
| **Video Pipeline** | Threaded reader (no buffer lag), supports file/webcam/RTSP/HTTP IP cam, output recording |
| **Observability** | Web dashboard (Flask), MJPEG stream, REST API, CSV+JSON logging, FPS monitoring |
| **Config** | JSON file, environment variables, CLI overrides |
| **DevOps** | Docker, headless mode, graceful shutdown, signal handling |

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ Video Source│───▶│   Detector   │───▶│ CentroidTracker │───▶│PeopleCounter │
│ (File/Cam/  │    │(MobileNet/   │    │  + TrackableObj │    │(Enter/Exit)  │
│  IP/RTSP)   │    │ HOG/YOLO)    │    │                 │    │              │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────┬───────┘
                                                                    │
                              ┌─────────────────────────────────────┼──────────────────┐
                              │                                     │                  │
                        ┌─────▼─────┐                         ┌─────▼─────┐     ┌────▼────┐
                        │   Web UI  │                         │  Logger   │     │  Alerts │
                        │ Flask+    │                         │ CSV+JSON  │     │Email/   │
                        │ Chart.js  │                         │           │     │Webhook  │
                        └───────────┘                         └───────────┘     └─────────┘
```

### Component Diagram

```
crowd_control/
├── detector.py      → Abstraction: PersonDetector.get() factory → MobileNetSSDetector / HOGDetector / YOLODetector
├── video.py         → VideoManager → ThreadingClass (queue-based, buffer=1) → unified .read() -> (ret, frame)
├── centroidtracker.py → scipy.spatial.distance.cdist matching, maxDisappeared, maxDistance
├── trackableobject.py → centroid history (30), timestamps, direction, speed
├── counter.py       → PeopleCounter.update(rects, H) → checks line crossing, manages events, threshold
├── mailer.py        → Mailer.alert() → email with cooldown + webhook POST
├── webapp.py        → Flask app, AppState (thread-safe frame/stats), /video_feed MJPEG, /api/stats
├── utils.py         → draw_counts(), draw_detections(), DataLogger
└── config.py        → AppConfig dataclass, from_env(), from_dict(), load_config()
```

---

## 🛠️ Tech Stack

- **Core:** Python 3.8+, OpenCV 4.5+ (headless for server), NumPy <2, SciPy
- **CV:** MobileNet SSD Caffe model, HOGDescriptor, optional dlib correlation_tracker, optional ultralytics YOLO
- **Video:** imutils (optional, for resize), threading, queue
- **Web:** Flask 2.0+, Chart.js (CDN), Bootstrap 5
- **Utils:** schedule, requests, smtplib, csv/json logging
- **Dev:** pytest, Docker, gdown (model download)

---

## 📁 Project Structure

```
crowd-control-system/
├── crowd_control/                 # Main package (v2.0)
│   ├── __init__.py               # Public API exports
│   ├── centroidtracker.py        # Centroid tracking with Hungarian-like matching
│   ├── trackableobject.py        # Trackable object with history
│   ├── detector.py               # Multi-backend detector factory
│   ├── counter.py                # Occupancy counting logic
│   ├── video.py                  # Threaded video I/O
│   ├── mailer.py                 # Alerting system
│   ├── config.py                 # Configuration management
│   ├── webapp.py                 # Flask dashboard & API
│   └── utils.py                  # Drawing & logging utilities
├── mylib/                        # Backward compatibility shim (v1 imports)
│   ├── __init__.py               # Re-exports from crowd_control
│   ├── centroidtracker.py
│   ├── trackableobject.py
│   ├── mailer.py
│   ├── config.py
│   └── thread.py
├── templates/
│   └── dashboard.html            # Real-time dashboard (Bootstrap + Chart.js)
├── static/                       # Static assets (placeholder)
├── scripts/
│   └── download_models.py        # Model downloader
├── tests/
│   └── test_basic.py             # Unit tests (tracker, counter, detector, config, mailer)
├── main.py                       # Primary entry point (v2.0) - RECOMMENDED
├── Run.py                        # Legacy entry point (v1 fixed, backward compat)
├── app.py                        # Web-only entry (dashboard demo)
├── config.json                   # Default configuration file
├── requirements.txt              # Modern dependencies
├── Dockerfile                    # Production container
├── .gitignore
├── FIXES_AND_FEATURES.md         # Detailed v1→v2 changelog
└── README.md                     # This file
```

**Root shims:** `centroidtracker.py`, `trackableobject.py`, `mailer.py`, `config.py`, `thread.py` at root re-export from `crowd_control/` for backward compatibility with old scripts that did `import centroidtracker`.

---

## 📦 Installation

### Prerequisites

- Python 3.8+ (3.11 tested)
- For GUI display: `libgl1` (Linux) or desktop OS. For headless/server: use `opencv-python-headless` (default in requirements)
- Optional: `dlib` for correlation tracking (better ID persistence, but heavy)

### Option 1: Development Install

```bash
# Clone
git clone https://github.com/aikanii/crowd-control-system.git
cd crowd-control-system

# Virtual env (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Core deps
pip install -r requirements.txt

# Verify
python tests/test_basic.py
# Expected: ✅ All tests passed!
```

### Option 2: Production / Server (Headless)

```bash
pip install opencv-python-headless numpy==1.26.4 scipy imutils Flask requests schedule
# Already in requirements.txt - headless is default
python main.py --input video.mp4 --no-display --web --web-host 0.0.0.0
```

### Option 3: Docker

```bash
docker build -t crowd-control:v2 .
docker run -p 5000:5000 -v $(pwd)/videos:/app/videos crowd-control:v2 \
  python main.py --input /app/videos/sample.mp4 --web --web-host 0.0.0.0 --no-display

# Or with env config
docker run -p 5000:5000 -e MAIL=alert@example.com -e CROWD_THRESHOLD=20 crowd-control:v2
```

### Option 4: Download Models (Optional, for best accuracy)

HOG works out-of-box with no downloads. For MobileNet SSD (more accurate):

```bash
python scripts/download_models.py
# Downloads to models/
#   models/MobileNetSSD_deploy.prototxt
#   models/MobileNetSSD_deploy.caffemodel

# Or manual:
mkdir -p models
wget https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt -O models/MobileNetSSD_deploy.prototxt
wget https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel -O models/MobileNetSSD_deploy.caffemodel
```

For YOLOv8:

```bash
pip install ultralytics
# Model auto-downloads on first use (yolov8n.pt)
```

---

## 🚀 Quick Start

### 1. Webcam with Threshold 10

```bash
python main.py --camera 0 --threshold 10
# Keys: q=quit, r=reset counts
```

### 2. Video File with Output Recording + Web Dashboard

```bash
python main.py --input sample.mp4 --output result.mp4 --threshold 20 --web --web-port 5000
# Open http://localhost:5000
```

### 3. IP Camera (RTSP/HTTP)

```bash
python main.py --camera "http://192.168.1.100:8080/video" --threshold 15 --detector auto
# Try --no-thread if stream unstable
```

### 4. Headless Server Mode

```bash
python main.py --input video.mp4 --no-display --web --web-host 0.0.0.0 --log occupancy.csv
```

### 5. Legacy Runner (Backward Compat)

```bash
python Run.py --input video.mp4 --no-display
# Or with models:
python Run.py --prototxt models/MobileNetSSD_deploy.prototxt --model models/MobileNetSSD_deploy.caffemodel --input video.mp4
```

---

## ⚙️ Configuration

### Priority Order (highest last, overrides)

1. `config.json` defaults
2. Environment variables
3. CLI arguments

### config.json Schema

```json
{
  "MAIL": "",                      // Alert recipient email
  "EMAIL_SENDER": "",              // SMTP sender (Gmail)
  "EMAIL_PASSWORD": "",            // App password
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 465,
  "ALERT": false,                  // Enable email alerts
  "ALERT_COOLDOWN": 60,            // Seconds between alerts
  "url": "",                       // IP camera URL
  "camera_id": 0,                  // Webcam ID
  "input_path": null,              // Video file path
  "output_path": null,             // Output video path
  "Threshold": 10,                 // Max occupancy
  "max_disappeared": 40,           // Tracker: frames before deregister
  "max_distance": 50,              // Tracker: max centroid distance
  "confidence": 0.4,               // Detector confidence threshold
  "skip_frames": 30,               // Detect every N frames (tracking between)
  "line_position_ratio": 0.5,      // Counting line Y ratio (0.5 = middle)
  "Thread": true,                  // Use threaded reader
  "Log": true,                     // Enable CSV/JSON logging
  "Scheduler": false,              // Auto-run at schedule_time
  "Timer": false,                  // Auto-stop after timer_seconds
  "timer_seconds": 28800,          // 8 hours
  "detector_type": "auto",         // auto|mobilenet|hog|yolo
  "use_dlib": true,                // Use dlib if available
  "web_enabled": true,             // Enable web dashboard
  "web_host": "0.0.0.0",
  "web_port": 5000,
  "log_file": "Log.csv",
  "log_json": "occupancy_log.json",
  "webhook_url": ""                // Slack/Discord webhook
}
```

### Environment Variables

| Env Var | Config Field | Example |
|---------|--------------|---------|
| `MAIL` | `MAIL` | `alert@example.com` |
| `EMAIL_SENDER` | `EMAIL_SENDER` | `sender@gmail.com` |
| `EMAIL_PASSWORD` | `EMAIL_PASSWORD` | `app-password` |
| `CROWD_THRESHOLD` | `Threshold` | `20` |
| `CROWD_CAMERA_URL` | `url` | `http://192.168.1.10/video` |
| `CROWD_WEB_PORT` | `web_port` | `5000` |
| `CROWD_INPUT` | `input_path` | `/data/video.mp4` |

```bash
export MAIL="security@company.com"
export EMAIL_SENDER="noreply@company.com"
export EMAIL_PASSWORD="xxxx xxxx xxxx xxxx"
export CROWD_THRESHOLD=25
python main.py --web
```

### Gmail App Password Setup

1. Enable 2FA on Google Account
2. Go to https://myaccount.google.com/apppasswords
3. Create app password for "Mail"
4. Use 16-char password in `EMAIL_PASSWORD` (no spaces)

---

## 💻 Usage

### CLI

```bash
python main.py --help

Options:
  -p, --prototxt PROTOTXT       Caffe prototxt path
  -m, --model MODEL             Caffe model path
  -i, --input INPUT             Video file path
  -c, --camera CAMERA           Camera ID (0) or IP URL
  -o, --output OUTPUT           Output video path
  --confidence CONFIDENCE       Detection confidence (0.4)
  -s, --skip-frames N           Detect every N frames (30)
  -t, --threshold N             Occupancy threshold (10)
  --detector {auto,mobilenet,hog,yolo}  Backend
  --no-thread                   Disable threaded reading
  --no-dlib                     Disable dlib tracker
  --web                         Enable web dashboard
  --web-host HOST               Web host (0.0.0.0)
  --web-port PORT               Web port (5000)
  --mail EMAIL                  Alert recipient
  --no-display                  Headless (no cv2.imshow)
  --log PATH                    CSV log path
  --config PATH                 Config JSON path
  --max-disappeared N           Tracker param (40)
  --max-distance N              Tracker param (50)
```

### Python API

```python
from crowd_control import PeopleCounter, get_detector
from crowd_control.video import VideoManager
from crowd_control.config import load_config

# Load config
config = load_config("config.json")
config.Threshold = 15

# Detector (auto fallback: MobileNet -> HOG)
detector = get_detector(detector_type="auto", confidence=0.4)
# detector = get_detector("hog")  # Always works
# detector = get_detector("yolo") # Requires ultralytics

# Counter
counter = PeopleCounter(threshold=config.Threshold, max_disappeared=40, max_distance=50)

# Video
vm = VideoManager(source="video.mp4", threaded=True).start()

while True:
    ret, frame = vm.read()
    if not ret:
        break
    
    rects = detector.detect(frame)  # List[(x1,y1,x2,y2)]
    stats = counter.update(rects, frame_height=frame.shape[0])
    
    print(f"Enter: {stats['enter']}, Exit: {stats['exit']}, Occupancy: {stats['occupancy']}, Alert: {stats['alert']}")
    
    if stats['alert']:
        # Trigger webhook/email via Mailer
        from crowd_control.mailer import Mailer
        Mailer().alert(recipient="alert@example.com", current_count=stats['occupancy'], threshold=config.Threshold)

vm.stop()
```

### REST API

When running with `--web`:

| Endpoint | Method | Description | Example |
|----------|--------|-------------|---------|
| `/` | GET | Dashboard HTML | Browser |
| `/video_feed` | GET | MJPEG stream | `<img src="/video_feed">` |
| `/api/stats` | GET | JSON stats | `{"enter":5,"exit":2,"occupancy":3,"threshold":10,"alert":false,"fps":12.3}` |
| `/api/threshold` | POST | Update threshold | `{"threshold":20}` |
| `/health` | GET | Health check | `{"status":"ok"}` |

```bash
# Get stats
curl http://localhost:5000/api/stats

# Set threshold
curl -X POST http://localhost:5000/api/threshold -H "Content-Type: application/json" -d '{"threshold":25}'

# Embed video feed in your own page
<img src="http://localhost:5000/video_feed" />
```

### Web Dashboard

`templates/dashboard.html` features:

- Live video with bounding boxes & ID labels
- Stats cards: Enter, Exit, Occupancy, Threshold
- Real-time occupancy chart (Chart.js, last 20 points)
- Alert banner (red pulse when threshold exceeded)
- Recent events list
- Threshold update input
- Bootstrap 5 responsive dark theme

To customize: edit `templates/dashboard.html` or mount your own `templates/` folder.

---

## 🔬 Detector Backends

| Backend | Accuracy | Speed | Dependencies | Best For |
|---------|----------|-------|--------------|----------|
| **MobileNet SSD** | High | Medium (CPU ~10 FPS) | `models/*.prototxt,*.caffemodel` | Production, balanced |
| **HOG** | Medium | Fast (CPU ~15 FPS) | None (OpenCV built-in) | Fallback, no model, edge devices |
| **YOLOv8** | Very High | Slow CPU / Fast GPU | `ultralytics`, `yolov8n.pt` auto-download | GPU servers, highest accuracy |
| **Auto** | - | - | Tries MobileNet → HOG | Recommended (robust) |

**Selection logic in `get_detector()`:**

```python
def get_detector(type="auto"):
    if type=="yolo" and has_ultralytics: return YOLO
    if type in ("mobilenet","auto") and models exist: return MobileNetSSD
    return HOG  # Always works
```

**Benchmark (i7 CPU, 600px width):**

- HOG: ~15 FPS, 0.3s per detection
- MobileNet SSD: ~8-12 FPS, 0.08s per detection + tracking
- YOLOv8n CPU: ~2-3 FPS, YOLOv8n GPU: ~25 FPS

---

## 👨‍💻 Development

### Setup Dev Environment

```bash
git clone https://github.com/aikanii/crowd-control-system.git
cd crowd-control-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest black flake8  # dev tools

# Run tests
pytest tests/ -v
python tests/test_basic.py

# Lint
black crowd_control/ main.py
flake8 crowd_control/
```

### Adding a New Detector

1. Create class in `crowd_control/detector.py`:

```python
class MyCustomDetector(PersonDetector):
    def __init__(self, confidence=0.4):
        super().__init__(confidence)
        # load model
    
    def detect(self, frame) -> List[Tuple[int,int,int,int]]:
        # return bounding boxes
        return [(x1,y1,x2,y2), ...]
```

2. Register in factory:

```python
def get_detector(...):
    if detector_type=="mycustom":
        return MyCustomDetector(confidence)
    ...
```

3. Test:

```python
det = get_detector("mycustom")
assert isinstance(det.detect(np.zeros((100,100,3),dtype=np.uint8)), list)
```

### Project Conventions

- Type hints everywhere
- Docstrings for public methods
- Logging via `logging` module, not print (except CLI info)
- Graceful fallback, never crash on missing optional dep
- Thread-safe where shared (AppState uses Lock)

### Testing

```bash
# Unit tests
python tests/test_basic.py

# Integration with dummy video
python -c "
import cv2, numpy as np
fourcc=cv2.VideoWriter_fourcc(*'mp4v')
out=cv2.VideoWriter('test.mp4',fourcc,10,(500,400))
for i in range(30):
    f=np.zeros((400,500,3),dtype=np.uint8)
    cv2.rectangle(f,(200,i*5,250,i*5+50),(255,255,255),-1)
    out.write(f)
out.release()
"
python main.py --input test.mp4 --no-display --detector hog --skip-frames 2
# Check Log.csv, occupancy_log.json created
```

---

## 🚢 Deployment

### Bare Metal / VM

```bash
# Systemd service example /etc/systemd/system/crowd.service
[Unit]
Description=Crowd Control System
After=network.target

[Service]
WorkingDirectory=/opt/crowd-control-system
Environment=MAIL=alert@company.com
Environment=EMAIL_SENDER=noreply@company.com
Environment=EMAIL_PASSWORD=apppass
ExecStart=/opt/crowd-control-system/venv/bin/python main.py --camera 0 --threshold 20 --web --web-host 0.0.0.0 --web-port 5000 --no-display
Restart=always

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
version: '3.8'
services:
  crowd:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MAIL=alert@example.com
      - CROWD_THRESHOLD=15
      - EMAIL_SENDER=sender@gmail.com
      - EMAIL_PASSWORD=apppass
    volumes:
      - ./videos:/app/videos
      - ./logs:/app/logs
    command: python main.py --input /app/videos/entrance.mp4 --web --web-host 0.0.0.0 --no-display --log /app/logs/Log.csv
```

### Kubernetes (Edge)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crowd-control
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crowd
  template:
    spec:
      containers:
      - name: crowd
        image: crowd-control:v2
        ports:
        - containerPort: 5000
        env:
        - name: CROWD_CAMERA_URL
          value: "rtsp://camera:554/stream"
```

---

## 🔧 Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `libGL.so.1: cannot open` | Using `opencv-python` on headless server | Use `opencv-python-headless` (default in requirements) or `apt-get install libgl1` |
| `No module named 'dlib'` | dlib not installed | System works without it (centroid only). Install via `conda install -c conda-forge dlib` or skip |
| `MobileNet model not found` | Models not downloaded | Run `python scripts/download_models.py` or use `--detector hog` (no model needed) |
| IP camera `Unable to open` | Wrong URL or threading issue | Try `--no-thread`, check URL in VLC first, use `rtsp://` or `http://` |
| Web dashboard shows no video | Running `app.py` not `main.py --web` | `app.py` is demo only, need `main.py --web` for live feed |
| Email not sending | Gmail blocks less secure apps | Use App Password, enable 2FA, check `EMAIL_SENDER` and `EMAIL_PASSWORD` |
| `numpy.core.multiarray failed` | NumPy 2.x incompatible with opencv 4.8 | Use `numpy<2` as in requirements |
| Low FPS | High resolution or heavy detector | Resize width to 500-600, increase `--skip-frames 30`, use HOG or MobileNet not YOLO CPU |

**Debug mode:**

```bash
python main.py --input video.mp4 --detector hog --no-display -v  # verbose logs
# Check logs: Log.csv, occupancy_log.json
```

---

## 🗺️ Roadmap

- [x] v2.0 - Fix critical bugs, add web dashboard, multi-backend, Docker
- [ ] v2.1 - Multi-line / multi-zone counting, direction zones
- [ ] v2.2 - Heatmap & density estimation
- [ ] v2.3 - Person re-identification (avoid double count)
- [ ] v2.4 - MQTT + WebSocket for IoT integration
- [ ] v2.5 - Database backend (SQLite/Postgres) + Grafana dashboard
- [ ] v3.0 - GPU acceleration, TensorRT, DeepSORT tracker

Contributions welcome! See [Contributing](#-contributing).

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing-detector`
3. Commit: `git commit -m "feat: add MyDetector backend"`
4. Push: `git push origin feature/amazing-detector`
5. Open PR

**PR Checklist:**

- [ ] Tests pass (`python tests/test_basic.py`)
- [ ] Code formatted with `black`
- [ ] No hard dependency added without fallback
- [ ] README updated if new feature
- [ ] Works in headless mode (`--no-display`)

---

## 📝 Changelog

See [FIXES_AND_FEATURES.md](FIXES_AND_FEATURES.md) for detailed v1→v2 bug fixes and new features.

**v2.0 (2024-09):**

- Fixed 9 critical bugs (undefined `i`, threading, counting logic, logging, mailer, imports, dlib hard dep, headless crash, outdated requirements)
- Added: multi-backend detector, web dashboard, REST API, threaded video, robust config, Docker, tests, modern CLI

---

## 📄 License

MIT License - see [LICENSE](LICENSE) (if present) or use as you wish. Attribution appreciated.

Original v1 by [aikanii](https://github.com/aikanii). v2.0 rewrite with production hardening.

---

## 🙏 Acknowledgments

- OpenCV community for MobileNet SSD & HOG
- Adrian Rosebrock (pyimagesearch) for centroid tracker inspiration
- Ultralytics for YOLOv8
- Flask & Chart.js for dashboard

---

**Made with ❤️ for safer, smarter crowds**

> For issues, feature requests, or questions, open an issue on GitHub or contact via email in config.
