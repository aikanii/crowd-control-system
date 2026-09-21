"""
Web Dashboard - Flask app for real-time monitoring
"""
import cv2
import time
import threading
import logging
from flask import Flask, Response, jsonify, render_template, request
from typing import Optional
import os

logger = logging.getLogger(__name__)

# Global state shared with main app
class AppState:
    def __init__(self):
        self.frame = None
        self.stats = {
            "enter": 0,
            "exit": 0,
            "occupancy": 0,
            "threshold": 10,
            "alert": False,
            "fps": 0
        }
        self.lock = threading.Lock()
        self.running = False

    def update_frame(self, frame):
        with self.lock:
            self.frame = frame.copy() if frame is not None else None

    def update_stats(self, stats):
        with self.lock:
            self.stats.update(stats)

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def get_stats(self):
        with self.lock:
            return self.stats.copy()

app_state = AppState()

def create_app():
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

    @app.route('/')
    def index():
        return render_template('dashboard.html')

    @app.route('/api/stats')
    def stats():
        return jsonify(app_state.get_stats())

    @app.route('/api/threshold', methods=['POST'])
    def set_threshold():
        data = request.get_json()
        if not data or 'threshold' not in data:
            return jsonify({"error": "threshold required"}), 400
        try:
            thresh = int(data['threshold'])
            with app_state.lock:
                app_state.stats['threshold'] = thresh
            return jsonify({"threshold": thresh})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route('/video_feed')
    def video_feed():
        def generate():
            while True:
                frame = app_state.get_frame()
                if frame is None:
                    # Placeholder black frame
                    import numpy as np
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "No feed - waiting for camera...", (50, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:
                    # Encode as JPEG
                    pass

                # Ensure JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.05)  # ~20 fps for stream

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/health')
    def health():
        return jsonify({"status": "ok", "running": app_state.running})

    return app

def run_web(host="0.0.0.0", port=5000, debug=False):
    app = create_app()
    logger.info(f"Starting web dashboard on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)

def start_web_thread(host="0.0.0.0", port=5000):
    thread = threading.Thread(target=run_web, kwargs={"host": host, "port": port}, daemon=True)
    thread.start()
    app_state.running = True
    return thread
