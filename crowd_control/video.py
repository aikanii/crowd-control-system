"""
Video handling - Threaded video capture and unified interface
"""
import cv2
import threading
import queue
import time
import logging
from typing import Optional, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)

try:
    from imutils.video import VideoStream
    HAS_IMUTILS_VS = True
except ImportError:
    HAS_IMUTILS_VS = False


class ThreadingClass:
    """
    Improved threaded video reader
    - Removes OpenCV internal buffer lag
    - Graceful shutdown
    - Supports both file and camera
    """
    def __init__(self, src: Union[str, int] = 0, queue_size: int = 128):
        self.src = src
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise ValueError(f"Unable to open video source: {src}")

        # Set buffer size to 1 to reduce lag
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.q = queue.Queue(maxsize=queue_size)
        self.stopped = False
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()
        logger.info(f"Threaded reader started for source: {src}")

    def _reader(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                logger.info("End of stream or read failed")
                self.stop()
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            try:
                self.q.put(frame, timeout=0.1)
            except queue.Full:
                continue

    def read(self) -> Optional[np.ndarray]:
        """Fetch frame from queue, blocking"""
        try:
            return self.q.get(timeout=5.0)
        except queue.Empty:
            if self.stopped:
                return None
            logger.warning("Queue empty but not stopped, returning None")
            return None

    def is_opened(self) -> bool:
        return not self.stopped and self.cap.isOpened()

    def stop(self):
        self.stopped = True

    def release(self):
        self.stop()
        # Wait a bit for thread to finish
        if self.t.is_alive():
            self.t.join(timeout=1.0)
        self.cap.release()
        logger.info("Threaded reader released")


class VideoManager:
    """
    Unified video source manager
    Handles: webcam, video file, IP camera, threaded vs non-threaded
    """
    def __init__(self, source: Union[str, int, None] = None, threaded: bool = True, camera_url: str = ""):
        self.source = source
        self.camera_url = camera_url
        self.threaded = threaded
        self.vs = None
        self.is_file = False
        self.cap = None

    def start(self):
        # Determine source
        src = self.source
        if src is None:
            if self.camera_url:
                src = self.camera_url
            else:
                src = 0  # default webcam

        # Check if file
        if isinstance(src, str) and src.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            self.is_file = True
            if self.threaded:
                logger.info(f"Opening video file with threading: {src}")
                self.vs = ThreadingClass(src)
            else:
                logger.info(f"Opening video file: {src}")
                self.vs = cv2.VideoCapture(src)
        else:
            # Camera / IP camera
            self.is_file = False
            if self.threaded:
                logger.info(f"Opening camera stream with threading: {src}")
                try:
                    self.vs = ThreadingClass(src)
                except Exception as e:
                    logger.warning(f"Threaded open failed: {e}, trying direct")
                    self.vs = cv2.VideoCapture(src)
                    self.threaded = False
            else:
                if HAS_IMUTILS_VS and isinstance(src, str) and src.startswith("http"):
                    logger.info(f"Opening IP camera via VideoStream: {src}")
                    self.vs = VideoStream(src).start()
                    time.sleep(2.0)
                else:
                    logger.info(f"Opening video source: {src}")
                    self.vs = cv2.VideoCapture(src)

        # Wait for first frame to confirm
        time.sleep(0.5)
        return self

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Returns (ret, frame) like cv2.VideoCapture
        For compatibility with old code that did frame[1] if input
        """
        if self.vs is None:
            return False, None

        if isinstance(self.vs, ThreadingClass):
            frame = self.vs.read()
            if frame is None:
                return False, None
            return True, frame
        elif HAS_IMUTILS_VS and hasattr(self.vs, 'read') and not isinstance(self.vs, cv2.VideoCapture):
            # imutils VideoStream returns frame directly
            frame = self.vs.read()
            if frame is None:
                return False, None
            return True, frame
        else:
            # cv2.VideoCapture
            ret, frame = self.vs.read()
            return ret, frame

    def get_frame(self) -> Optional[np.ndarray]:
        ret, frame = self.read()
        return frame if ret else None

    def is_opened(self) -> bool:
        if self.vs is None:
            return False
        if isinstance(self.vs, ThreadingClass):
            return self.vs.is_opened()
        if isinstance(self.vs, cv2.VideoCapture):
            return self.vs.isOpened()
        return True  # assume VideoStream is opened

    def stop(self):
        if self.vs is None:
            return
        try:
            if isinstance(self.vs, ThreadingClass):
                self.vs.release()
            elif isinstance(self.vs, cv2.VideoCapture):
                self.vs.release()
            elif HAS_IMUTILS_VS:
                # VideoStream
                self.vs.stop()
        except Exception as e:
            logger.warning(f"Error stopping video: {e}")
        self.vs = None

    def release(self):
        self.stop()

    def __del__(self):
        self.stop()
