"""
Crowd Control System - Modern People Counting & Occupancy Monitoring
"""

__version__ = "2.0.0"
__author__ = "Crowd Control Team"

from .centroidtracker import CentroidTracker
from .trackableobject import TrackableObject
from .config import AppConfig, load_config
from .counter import PeopleCounter
from .detector import PersonDetector, get_detector

__all__ = [
    "CentroidTracker",
    "TrackableObject",
    "AppConfig",
    "load_config",
    "PeopleCounter",
    "PersonDetector",
    "get_detector",
]
