"""
Utilities - Drawing, logging, helpers
"""
import cv2
import numpy as np
import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def draw_counts(frame: np.ndarray, stats: Dict, line_y: int, status: str = "Tracking", fps: float = 0) -> np.ndarray:
    H, W = frame.shape[:2]

    # Draw line
    cv2.line(frame, (0, line_y), (W, line_y), (0, 255, 255), 2)
    cv2.putText(frame, "Counting Line", (10, line_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

    # Draw objects
    objects = stats.get("objects", {})
    trackable = stats.get("trackable", {})

    for (objectID, centroid) in objects.items():
        to = trackable.get(objectID, None)
        # Determine color based on counted
        color = (0, 255, 0) if to and to.counted else (255, 255, 255)
        if to and to.direction == "up":
            color = (255, 0, 0)
        elif to and to.direction == "down":
            color = (0, 0, 255)

        text = f"ID {objectID}"
        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.circle(frame, (centroid[0], centroid[1]), 4, color, -1)

        # Draw trail
        if to and len(to.centroids) > 1:
            pts = np.array(to.centroids, dtype=np.int32)
            cv2.polylines(frame, [pts], False, color, 1)

    # Info panel - left
    info = [
        ("Exit", stats.get("exit", 0)),
        ("Enter", stats.get("enter", 0)),
        ("Occupancy", stats.get("occupancy", 0)),
        ("Threshold", stats.get("threshold", 0)),
        ("Status", status),
    ]
    if fps:
        info.append(("FPS", f"{fps:.1f}"))

    for i, (k, v) in enumerate(info):
        text = f"{k}: {v}"
        y = H - ((i * 22) + 20)
        # Background for readability
        cv2.rectangle(frame, (5, y - 15), (200, y + 5), (0, 0, 0), -1)
        color = (0, 0, 255) if k == "Occupancy" and stats.get("alert") else (255, 255, 255)
        if k == "Occupancy" and stats.get("alert"):
            color = (0, 0, 255)
        cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # Alert
    if stats.get("alert"):
        cv2.rectangle(frame, (0, 0), (W, 40), (0, 0, 255), -1)
        cv2.putText(frame, "ALERT: People limit exceeded!", (10, 25),
                    cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 2)

    return frame


def draw_detections(frame: np.ndarray, rects: List[Tuple[int, int, int, int]]) -> np.ndarray:
    for (startX, startY, endX, endY) in rects:
        cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
    return frame


class DataLogger:
    def __init__(self, csv_path: str = "Log.csv", json_path: str = "occupancy_log.json"):
        self.csv_path = csv_path
        self.json_path = json_path
        self.entries = []

    def log(self, stats: Dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "enter": stats.get("enter", 0),
            "exit": stats.get("exit", 0),
            "occupancy": stats.get("occupancy", 0),
            "threshold": stats.get("threshold", 0)
        }
        self.entries.append(entry)
        logger.debug(f"Logged: {entry}")

    def save_csv(self):
        try:
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Enter", "Exit", "Occupancy", "Threshold"])
                for e in self.entries:
                    writer.writerow([e["timestamp"], e["enter"], e["exit"], e["occupancy"], e["threshold"]])
            logger.info(f"CSV log saved to {self.csv_path}")
        except Exception as ex:
            logger.error(f"Failed to save CSV: {ex}")

    def save_json(self):
        try:
            with open(self.json_path, 'w') as f:
                json.dump(self.entries, f, indent=2)
            logger.info(f"JSON log saved to {self.json_path}")
        except Exception as ex:
            logger.error(f"Failed to save JSON: {ex}")

    def save(self):
        self.save_csv()
        self.save_json()


def ensure_dir(path: str):
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
