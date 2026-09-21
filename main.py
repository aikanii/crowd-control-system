#!/usr/bin/env python3
"""
Crowd Control System - Main Entry Point (v2.0)

Features:
- Multiple detector backends (MobileNet SSD, HOG, YOLO)
- Robust tracking with fallback when dlib unavailable
- Threaded video capture
- Real-time occupancy counting
- Email & webhook alerts
- Web dashboard
- CSV/JSON logging
- FPS monitoring

Usage:
    python main.py --input video.mp4 --threshold 10
    python main.py --camera 0 --web --port 5000
    python main.py --help
"""

import argparse
import cv2
import time
import logging
import sys
import os
import signal
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Local imports
from crowd_control.config import AppConfig, load_config
from crowd_control.detector import get_detector
from crowd_control.counter import PeopleCounter
from crowd_control.video import VideoManager
from crowd_control.mailer import Mailer
from crowd_control.utils import draw_counts, draw_detections, DataLogger
from crowd_control.webapp import app_state, start_web_thread

# Try dlib tracker import (optional)
try:
    import dlib
    HAS_DLIB = True
    logger.info("dlib available - will use correlation trackers")
except ImportError:
    HAS_DLIB = False
    logger.warning("dlib not available - using centroid tracking only (lighter, still works)")

try:
    import imutils
    HAS_IMUTILS = True
except ImportError:
    HAS_IMUTILS = False

def parse_args():
    ap = argparse.ArgumentParser(description="Crowd Control System - People Counting")
    ap.add_argument("-p", "--prototxt", required=False, default=None,
                    help="path to Caffe 'deploy' prototxt file")
    ap.add_argument("-m", "--model", required=False, default=None,
                    help="path to Caffe pre-trained model")
    ap.add_argument("-i", "--input", type=str, default=None,
                    help="path to optional input video file")
    ap.add_argument("-c", "--camera", type=str, default=None,
                    help="camera id (0,1) or IP camera URL (http://...)")
    ap.add_argument("-o", "--output", type=str, default=None,
                    help="path to optional output video file")
    ap.add_argument("--confidence", type=float, default=0.4,
                    help="minimum probability to filter weak detections")
    ap.add_argument("-s", "--skip-frames", type=int, default=30,
                    help="# of skip frames between detections")
    ap.add_argument("-t", "--threshold", type=int, default=10,
                    help="max people inside threshold for alerts")
    ap.add_argument("--detector", type=str, default="auto", choices=["auto", "mobilenet", "hog", "yolo"],
                    help="detector backend")
    ap.add_argument("--no-thread", action="store_true",
                    help="disable threaded video reading")
    ap.add_argument("--no-dlib", action="store_true",
                    help="disable dlib correlation trackers even if available")
    ap.add_argument("--web", action="store_true",
                    help="enable web dashboard")
    ap.add_argument("--web-host", type=str, default="0.0.0.0",
                    help="web dashboard host")
    ap.add_argument("--web-port", type=int, default=5000,
                    help="web dashboard port")
    ap.add_argument("--mail", type=str, default="",
                    help="email to send alerts to")
    ap.add_argument("--no-display", action="store_true",
                    help="don't display video window (headless)")
    ap.add_argument("--log", type=str, default="Log.csv",
                    help="log file path")
    ap.add_argument("--config", type=str, default=None,
                    help="path to config.json")
    ap.add_argument("--max-disappeared", type=int, default=40,
                    help="max frames object can disappear before deregister")
    ap.add_argument("--max-distance", type=int, default=50,
                    help="max distance for centroid matching")
    return ap.parse_args()

class FPSCounter:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0

    def update(self):
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 1.0:
            self.fps = self.frame_count / elapsed
            # Reset every 2 seconds for moving avg
            if elapsed > 2.0:
                self.start_time = time.time()
                self.frame_count = 0

    def get_fps(self):
        return self.fps

def run_counter(args, app_config: AppConfig):
    # Override config with args
    threshold = args.threshold or app_config.Threshold
    input_path = args.input or app_config.input_path
    output_path = args.output or app_config.output_path
    prototxt = args.prototxt or app_config.prototxt
    model = args.model or app_config.model
    confidence = args.confidence or app_config.confidence
    skip_frames = args.skip_frames or app_config.skip_frames
    threaded = not args.no_thread
    use_dlib = HAS_DLIB and not args.no_dlib and app_config.use_dlib

    # Determine source
    source = None
    if input_path:
        source = input_path
        logger.info(f"Input video: {input_path}")
    elif args.camera:
        # Try to parse as int for webcam
        try:
            source = int(args.camera)
        except ValueError:
            source = args.camera
        logger.info(f"Camera source: {source}")
    elif app_config.url:
        source = app_config.url
        logger.info(f"IP Camera URL from config: {source}")
    else:
        source = app_config.camera_id
        logger.info(f"Using default camera id: {source}")

    # Detector
    detector = get_detector(detector_type=args.detector, prototxt=prototxt, model=model, confidence=confidence)
    logger.info(f"Detector ready: {detector.__class__.__name__}")

    # Counter
    counter = PeopleCounter(
        max_disappeared=args.max_disappeared,
        max_distance=args.max_distance,
        threshold=threshold,
        line_ratio=app_config.line_position_ratio
    )

    # Video
    video_manager = VideoManager(source=source, threaded=threaded, camera_url=app_config.url)
    try:
        video_manager.start()
    except Exception as e:
        logger.error(f"Failed to start video source {source}: {e}")
        return

    # Writer
    writer = None
    W = H = None

    # Trackers for dlib mode
    trackers = []

    # FPS
    fps_counter = FPSCounter()

    # Logger
    data_logger = DataLogger(csv_path=args.log, json_path=app_config.log_json)

    # Mailer
    mailer = Mailer(
        email=app_config.EMAIL_SENDER or app_config.MAIL,
        password=app_config.EMAIL_PASSWORD,
        sender=app_config.EMAIL_SENDER
    )
    alert_recipient = args.mail or app_config.MAIL
    webhook_url = app_config.webhook_url

    # Web dashboard
    if args.web or app_config.web_enabled:
        try:
            start_web_thread(host=args.web_host or app_config.web_host, port=args.web_port or app_config.web_port)
            logger.info(f"Web dashboard at http://{args.web_host}:{args.web_port}")
        except Exception as e:
            logger.warning(f"Failed to start web dashboard: {e}")

    totalFrames = 0
    last_alert = 0
    alert_cooldown = app_config.ALERT_COOLDOWN

    logger.info("Starting main loop. Press 'q' to quit.")

    # Graceful shutdown
    should_stop = False
    def signal_handler(sig, frame):
        nonlocal should_stop
        logger.info("Interrupt received, stopping...")
        should_stop = True
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while not should_stop:
            ret, frame = video_manager.read()
            if not ret or frame is None:
                if input_path:
                    logger.info("End of video file")
                    break
                else:
                    logger.warning("Failed to read frame, retrying...")
                    time.sleep(0.1)
                    continue

            # Resize for speed
            if HAS_IMUTILS:
                frame = imutils.resize(frame, width=600)
            else:
                # Keep aspect ratio, width 600
                h, w = frame.shape[:2]
                if w > 600:
                    ratio = 600 / w
                    frame = cv2.resize(frame, (600, int(h * ratio)))

            if W is None or H is None:
                (H, W) = frame.shape[:2]
                logger.info(f"Frame size: {W}x{H}")

            if output_path and writer is None:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(output_path, fourcc, 20, (W, H), True)
                logger.info(f"Writing output to {output_path}")

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            status = "Waiting"
            rects = []

            # Detection phase
            if totalFrames % skip_frames == 0:
                status = "Detecting"
                trackers = []
                rects = detector.detect(frame)

                # Initialize dlib trackers if available
                if use_dlib:
                    for (startX, startY, endX, endY) in rects:
                        tracker = dlib.correlation_tracker()
                        rect = dlib.rectangle(startX, startY, endX, endY)
                        tracker.start_track(rgb, rect)
                        trackers.append(tracker)
            else:
                # Tracking phase
                if use_dlib and trackers:
                    status = "Tracking"
                    for tracker in trackers:
                        tracker.update(rgb)
                        pos = tracker.get_position()
                        startX = int(pos.left())
                        startY = int(pos.top())
                        endX = int(pos.right())
                        endY = int(pos.bottom())
                        rects.append((startX, startY, endX, endY))
                else:
                    # If no dlib, we still have rects from last detection? 
                    # Actually for non-dlib mode, we detect every frame or rely on centroid tracker
                    # Let's detect every frame if not using dlib and skip_frames is high
                    # But to keep performance, if no dlib we detect every frame when rects empty
                    if not rects:
                        # In non-dlib mode, we need to detect more frequently or keep last rects
                        # For simplicity, detect now
                        rects = detector.detect(frame)
                        status = "Detecting"

            # Counter update
            line_y = int(H * app_config.line_position_ratio)
            stats = counter.update(rects, H)
            stats["fps"] = fps_counter.get_fps()
            stats["status"] = status

            # Log
            data_logger.log(stats)

            # Alert check
            if stats["alert"]:
                now = time.time()
                if now - last_alert > alert_cooldown:
                    logger.warning(f"ALERT: Occupancy {stats['occupancy']} >= threshold {threshold}")
                    if alert_recipient or webhook_url:
                        mailer.alert(alert_recipient, stats["occupancy"], threshold, webhook_url)
                    last_alert = now

            # Draw
            frame = draw_detections(frame, rects)
            frame = draw_counts(frame, stats, line_y, status=status, fps=fps_counter.get_fps())

            # Web update
            app_state.update_frame(frame)
            app_state.update_stats(stats)

            # Display
            if not args.no_display:
                try:
                    cv2.imshow("Crowd Control - Real-Time Monitoring", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        logger.info("q pressed, exiting")
                        break
                    elif key == ord("r"):
                        counter.reset()
                        logger.info("Counter reset by user")
                except cv2.error as e:
                    logger.warning(f"Display failed (headless?): {e}, switching to no-display mode")
                    args.no_display = True

            # Writer
            if writer is not None:
                writer.write(frame)

            totalFrames += 1
            fps_counter.update()

            # Timer check
            if app_config.Timer:
                if time.time() - fps_counter.start_time > app_config.timer_seconds:
                    logger.info("Timer expired, stopping")
                    break

    except Exception as e:
        logger.exception(f"Error in main loop: {e}")
    finally:
        logger.info("Cleaning up...")
        data_logger.save()
        video_manager.stop()
        if writer is not None:
            writer.release()
        try:
            cv2.destroyAllWindows()
        except:
            pass
        logger.info(f"Final stats - Enter: {counter.totalDown}, Exit: {counter.totalUp}, Occupancy: {counter.current_occupancy}")
        logger.info("Done.")

def main():
    args = parse_args()
    # Load config
    app_config = load_config(args.config)
    # Override with args
    if args.threshold:
        app_config.Threshold = args.threshold
    if args.input:
        app_config.input_path = args.input
    if args.output:
        app_config.output_path = args.output

    logger.info(f"Config: threshold={app_config.Threshold}, detector={args.detector}, threaded={not args.no_thread}")
    run_counter(args, app_config)

if __name__ == "__main__":
    main()
