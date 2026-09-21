# Crowd Control System v2.0 - People Counting & Occupancy Monitoring

Modern, fully functional crowd control system with real-time people counting, occupancy monitoring, alerts, and web dashboard.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ What's New in v2.0 (Bug Fixes & Features)

### 🐛 Bugs Fixed
- **Fixed undefined `i` variable** in `cv2.putText` that caused crash when no detections
- **Fixed VideoStream/Threading logic** - proper cleanup, no more resource leaks
- **Fixed counting logic** - `empty/empty1/x` confusion resolved, now accurate occupancy = Enter - Exit
- **Fixed Log.csv** overwriting every frame - now proper logging with CSV + JSON
- **Fixed Mailer crash** when no email configured - graceful fallback with cooldown
- **Fixed imports** - `mylib` module structure now works, backward compatible with root imports
- **Fixed frame reading** - unified `VideoManager` handles file, webcam, IP camera consistently
- **Fixed dlib dependency** - now optional, falls back to HOG + centroid tracking

### 🚀 New Features
- **Multiple detectors**: MobileNet SSD, HOG (always works), YOLOv8 (optional)
- **Web Dashboard** with live video feed, charts, stats (Flask)
- **REST API**: `/api/stats`, `/api/threshold`, `/video_feed`
- **Improved tracker**: Correlation tracker when dlib available, else pure centroid
- **Smart alerting**: Email with cooldown + webhook (Slack/Discord) + console
- **Data logging**: CSV + JSON with history
- **Threaded video**: No buffer lag, handles IP cameras
- **CLI**: Full argparse with `--web`, `--threshold`, `--detector` options
- **Config system**: JSON file + env vars
- **Docker ready**, modern requirements

---

## 📦 Installation

### 1. Clone & Install
```bash
git clone https://github.com/aikanii/crowd-control-system.git
cd crowd-control-system
pip install -r requirements.txt
```

### 2. (Optional) Download MobileNet SSD models for best accuracy
```bash
mkdir -p models
# Download prototxt
wget https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt -O models/MobileNetSSD_deploy.prototxt
# Download caffemodel (from opencv extra)
wget https://github.com/chuanqi305/MobileNet-SSD/raw/master/MobileNetSSD_deploy.caffemodel -O models/MobileNetSSD_deploy.caffemodel
# Or use script
python scripts/download_models.py
```
> **Note**: If models not found, system auto-falls back to HOG detector (no download needed, works out of box).

### 3. (Optional) Install dlib for better tracking
```bash
pip install dlib
# If fails, system still works with centroid tracking only
```

## 🚀 Quick Start

### Basic - Webcam
```bash
python main.py --camera 0 --threshold 10
# Press 'q' to quit, 'r' to reset counts
```

### With Video File
```bash
python main.py --input path/to/video.mp4 --output out.mp4 --threshold 20
```

### With Web Dashboard (Recommended)
```bash
python main.py --input video.mp4 --web --web-port 5000
# Open http://localhost:5000
```

### Legacy Runner (Fixed)
```bash
python Run.py --prototxt models/MobileNetSSD_deploy.prototxt --model models/MobileNetSSD_deploy.caffemodel --input video.mp4
# Or without models (uses HOG):
python Run.py --input video.mp4
```

### Web Only (Dashboard demo)
```bash
python app.py --port 5000
```

## ⚙️ Configuration

### config.json
Edit `config.json`:
```json
{
  "MAIL": "recipient@example.com",
  "EMAIL_SENDER": "sender@gmail.com",
  "EMAIL_PASSWORD": "app-password",
  "Threshold": 10,
  "url": "http://192.168.1.100:8080/video",
  "detector_type": "auto",
  "web_enabled": true
}
```

### Environment Variables
```bash
export MAIL="alert@example.com"
export EMAIL_SENDER="sender@gmail.com"
export EMAIL_PASSWORD="your-app-password"
export CROWD_THRESHOLD=15
export CROWD_CAMERA_URL="http://ip:port/video"
python main.py --web
```

### Email Alerts Setup (Gmail)
1. Enable 2FA
2. Create App Password: https://myaccount.google.com/apppasswords
3. Use that password in config

## 📊 How It Works

1. **Detection**: MobileNet SSD / HOG / YOLO detects people
2. **Tracking**: dlib correlation tracker + centroid tracker associates IDs
3. **Counting**: Virtual line in middle, direction determined by centroid history
   - Moving down + below line = Enter
   - Moving up + above line = Exit
4. **Occupancy**: Enter - Exit
5. **Alert**: If occupancy >= Threshold, email/webhook/console alert

## 🌐 Web Dashboard API

- `GET /` - Dashboard HTML
- `GET /video_feed` - MJPEG stream
- `GET /api/stats` - JSON: `{enter, exit, occupancy, threshold, alert, fps}`
- `POST /api/threshold` - Set threshold: `{"threshold": 20}`
- `GET /health` - Health check

## 📁 Project Structure

```
crowd-control-system/
├── crowd_control/          # Main package
│   ├── centroidtracker.py  # Centroid tracking
│   ├── trackableobject.py  # Object with history
│   ├── detector.py         # Multi-backend detector
│   ├── counter.py          # Counting logic
│   ├── video.py            # Threaded video capture
│   ├── mailer.py           # Alerts
│   ├── config.py           # Config management
│   ├── webapp.py           # Flask dashboard
│   └── utils.py            # Drawing & logging
├── mylib/                  # Backward compat shim
├── templates/
│   └── dashboard.html      # Web UI
├── main.py                 # New main entry (recommended)
├── Run.py                  # Legacy entry (fixed)
├── app.py                  # Web-only entry
├── config.json             # Config file
├── requirements.txt
└── README.md
```

## 🧪 Testing

```bash
# Test imports
python -c "from crowd_control import PeopleCounter, get_detector; print('OK')"

# Test detector fallback (no model needed)
python -c "from crowd_control.detector import get_detector; d=get_detector('hog'); print(d.__class__.__name__)"

# Test with synthetic video (creates black frames)
python main.py --no-display --threshold 5  # Will use webcam, press Ctrl+C
```

## 🐳 Docker (Optional)

```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "--web", "--web-host", "0.0.0.0", "--no-display"]
```

## 🔧 Troubleshooting

**Q: dlib fails to install?**
A: System works without it, using centroid tracking only. Install via `conda install dlib` or skip.

**Q: No MobileNet model?**
A: Uses HOG fallback automatically. Download models via script for better accuracy.

**Q: IP camera not opening?**
A: Check URL, try `python main.py --camera "http://..." --no-thread` (disable threading for some cameras).

**Q: Web dashboard not showing video?**
A: Ensure `main.py --web` running, not just `app.py`. Check firewall port 5000.

**Q: Email not sending?**
A: Check app password, enable less secure? Use webhook as alternative.

## 📈 Future Improvements

- [ ] Multi-zone counting
- [ ] People density heatmap
- [ ] Re-identification
- [ ] YOLOv8 integration by default
- [ ] MQTT support
- [ ] Database logging

## 🤝 Contributing

PRs welcome! Fix bugs, add detectors, improve UI.

## 📄 License

MIT

## 🙏 Credits

Original by aikanii, v2.0 modernized with bug fixes and new features.

---
**Made with ❤️ for safer crowds**
