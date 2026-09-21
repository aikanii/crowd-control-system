"""
TrackableObject - Enhanced with direction, speed and counting logic
"""
import numpy as np
from datetime import datetime
from typing import List, Tuple, Optional


class TrackableObject:
    def __init__(self, objectID: int, centroid: Tuple[int, int]):
        # store the object ID, then initialize a list of centroids
        # using the current centroid
        self.objectID = objectID
        self.centroids: List[Tuple[int, int]] = [centroid]
        self.timestamps: List[datetime] = [datetime.now()]

        # initialize a boolean used to indicate if the object has
        # already been counted or not
        self.counted = False
        self.direction: Optional[str] = None  # "up" or "down"
        self.counted_time: Optional[datetime] = None

    def update(self, centroid: Tuple[int, int]):
        self.centroids.append(centroid)
        self.timestamps.append(datetime.now())
        # keep only last 30 centroids to avoid memory bloat
        if len(self.centroids) > 30:
            self.centroids = self.centroids[-30:]
            self.timestamps = self.timestamps[-30:]

    def get_direction(self) -> float:
        """Return direction value: negative = up, positive = down"""
        if len(self.centroids) < 2:
            return 0
        y = [c[1] for c in self.centroids]
        # mean of previous vs current
        return self.centroids[-1][1] - float(np.mean(y[:-1]))

    def estimate_speed(self) -> float:
        """Estimate speed in pixels per second (approx)"""
        if len(self.centroids) < 2:
            return 0.0
        # distance between last two centroids / time delta
        c1 = np.array(self.centroids[-2])
        c2 = np.array(self.centroids[-1])
        dist = np.linalg.norm(c2 - c1)
        dt = (self.timestamps[-1] - self.timestamps[-2]).total_seconds()
        if dt == 0:
            return 0.0
        return dist / dt
