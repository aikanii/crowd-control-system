"""
Backward compatibility shim - old code imports from mylib
"""
from crowd_control.centroidtracker import CentroidTracker
from crowd_control.trackableobject import TrackableObject
from crowd_control.mailer import Mailer
from crowd_control.config import AppConfig, load_config, get_config
import crowd_control.config as config
from crowd_control.video import ThreadingClass
from crowd_control import video as thread

# For old code that does `from mylib import config, thread`
# config module already exposes MAIL etc

__all__ = ["CentroidTracker", "TrackableObject", "Mailer", "config", "thread", "ThreadingClass"]
