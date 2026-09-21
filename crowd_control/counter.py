"""
People Counter - Core counting logic with history and stats
"""
import numpy as np
import time
import logging
from collections import deque
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from .centroidtracker import CentroidTracker
from .trackableobject import TrackableObject

logger = logging.getLogger(__name__)


class PeopleCounter:
    def __init__(self, max_disappeared: int = 40, max_distance: int = 50, threshold: int = 10, line_ratio: float = 0.5):
        self.ct = CentroidTracker(maxDisappeared=max_disappeared, maxDistance=max_distance)
        self.trackableObjects: Dict[int, TrackableObject] = {}
        self.totalUp = 0
        self.totalDown = 0
        self.threshold = threshold
        self.line_ratio = line_ratio

        # For occupancy history
        self.occupancy_history = deque(maxlen=1000)
        self.events = deque(maxlen=500)  # list of events
        self.current_occupancy = 0

        # For alert cooldown
        self.last_alert_time = 0
        self.alert_active = False

    def update(self, rects: List[Tuple[int, int, int, int]], frame_height: int) -> Dict:
        """
        Update counter with new detections
        Returns dict with stats
        """
        objects = self.ct.update(rects)
        line_y = int(frame_height * self.line_ratio)

        for (objectID, centroid) in objects.items():
            to = self.trackableObjects.get(objectID, None)

            if to is None:
                to = TrackableObject(objectID, centroid)
            else:
                # Direction
                y_positions = [c[1] for c in to.centroids]
                direction = centroid[1] - np.mean(y_positions) if y_positions else 0
                to.update(centroid)

                if not to.counted:
                    # Moving up and above line -> exit
                    if direction < 0 and centroid[1] < line_y:
                        self.totalUp += 1
                        to.counted = True
                        to.direction = "up"
                        to.counted_time = datetime.now()
                        self.events.append({
                            "time": datetime.now().isoformat(),
                            "id": objectID,
                            "direction": "exit",
                            "centroid": centroid.tolist() if hasattr(centroid, 'tolist') else list(centroid)
                        })
                        logger.info(f"Object {objectID} exited. Total exits: {self.totalUp}")

                    # Moving down and below line -> enter
                    elif direction > 0 and centroid[1] > line_y:
                        self.totalDown += 1
                        to.counted = True
                        to.direction = "down"
                        to.counted_time = datetime.now()
                        self.events.append({
                            "time": datetime.now().isoformat(),
                            "id": objectID,
                            "direction": "enter",
                            "centroid": centroid.tolist() if hasattr(centroid, 'tolist') else list(centroid)
                        })
                        logger.info(f"Object {objectID} entered. Total enters: {self.totalDown}")

            self.trackableObjects[objectID] = to

        # Calculate occupancy
        self.current_occupancy = self.totalDown - self.totalUp
        self.occupancy_history.append({
            "timestamp": datetime.now().isoformat(),
            "occupancy": self.current_occupancy,
            "enter": self.totalDown,
            "exit": self.totalUp
        })

        # Check threshold
        alert_triggered = False
        if self.current_occupancy >= self.threshold:
            if not self.alert_active:
                logger.warning(f"Threshold exceeded! {self.current_occupancy} >= {self.threshold}")
            self.alert_active = True
            alert_triggered = True
        else:
            self.alert_active = False

        return {
            "enter": self.totalDown,
            "exit": self.totalUp,
            "occupancy": self.current_occupancy,
            "threshold": self.threshold,
            "alert": alert_triggered,
            "objects": objects,
            "trackable": self.trackableObjects
        }

    def get_stats(self) -> Dict:
        return {
            "enter": self.totalDown,
            "exit": self.totalUp,
            "occupancy": self.current_occupancy,
            "threshold": self.threshold,
            "alert": self.alert_active,
            "total_tracked": len(self.trackableObjects),
            "history": list(self.occupancy_history)[-100:],  # last 100
            "recent_events": list(self.events)[-20:]
        }

    def reset(self):
        self.totalUp = 0
        self.totalDown = 0
        self.current_occupancy = 0
        self.trackableObjects.clear()
        self.ct = CentroidTracker(maxDisappeared=self.ct.maxDisappeared, maxDistance=self.ct.maxDistance)
        self.occupancy_history.clear()
        self.events.clear()
        self.alert_active = False
        logger.info("Counter reset")

    def set_threshold(self, threshold: int):
        self.threshold = threshold
        logger.info(f"Threshold set to {threshold}")
