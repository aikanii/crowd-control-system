"""
Person Detector - Multiple backends with graceful fallback
Supports: MobileNet SSD (OpenCV DNN), HOG, YOLO (optional)
"""
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional
import os

logger = logging.getLogger(__name__)

# Try optional imports
try:
    import imutils
    HAS_IMUTILS = True
except ImportError:
    HAS_IMUTILS = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]


class PersonDetector:
    def __init__(self, confidence: float = 0.4):
        self.confidence = confidence

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Return list of bounding boxes (startX, startY, endX, endY)"""
        raise NotImplementedError


class MobileNetSSDetector(PersonDetector):
    def __init__(self, prototxt: Optional[str] = None, model: Optional[str] = None, confidence: float = 0.4):
        super().__init__(confidence)
        self.prototxt = prototxt
        self.model = model
        self.net = None

        # Try to find models in common locations
        possible_prototxt = [
            prototxt,
            "models/MobileNetSSD_deploy.prototxt",
            "MobileNetSSD_deploy.prototxt",
            "mylib/MobileNetSSD_deploy.prototxt",
        ]
        possible_model = [
            model,
            "models/MobileNetSSD_deploy.caffemodel",
            "MobileNetSSD_deploy.caffemodel",
            "mylib/MobileNetSSD_deploy.caffemodel",
        ]

        prototxt_path = next((p for p in possible_prototxt if p and os.path.exists(p)), None)
        model_path = next((p for p in possible_model if p and os.path.exists(p)), None)

        if prototxt_path and model_path:
            try:
                logger.info(f"Loading MobileNet SSD from {prototxt_path}, {model_path}")
                self.net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
                logger.info("MobileNet SSD loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load MobileNet SSD: {e}")
                self.net = None
        else:
            logger.warning(f"MobileNet SSD model files not found. Searched: {possible_prototxt}, {possible_model}")
            logger.warning("Will fallback to HOG detector. Download models via: python scripts/download_models.py")
            self.net = None

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.net is None:
            return []

        (H, W) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()

        rects = []
        for i in np.arange(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > self.confidence:
                idx = int(detections[0, 0, i, 1])
                if idx >= len(CLASSES):
                    continue
                if CLASSES[idx] != "person":
                    continue
                box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                (startX, startY, endX, endY) = box.astype("int")
                # Clamp to frame
                startX = max(0, startX)
                startY = max(0, startY)
                endX = min(W - 1, endX)
                endY = min(H - 1, endY)
                if endX > startX and endY > startY:
                    rects.append((startX, startY, endX, endY))
        return rects

    def is_loaded(self) -> bool:
        return self.net is not None


class HOGDetector(PersonDetector):
    def __init__(self, confidence: float = 0.4):
        super().__init__(confidence)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        logger.info("HOG detector initialized as fallback")

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        # HOG works better on larger images, but we resize for speed
        # Use 400 width if imutils available
        orig_frame = frame
        if HAS_IMUTILS:
            frame_small = imutils.resize(frame, width=min(400, frame.shape[1]))
        else:
            # Manual resize
            width = min(400, frame.shape[1])
            height = int(frame.shape[0] * width / frame.shape[1])
            frame_small = cv2.resize(frame, (width, height))

        (rects, weights) = self.hog.detectMultiScale(frame_small, winStride=(4, 4), padding=(8, 8), scale=1.05)

        # Scale back to original size
        if frame_small.shape[1] != orig_frame.shape[1]:
            scale_x = orig_frame.shape[1] / frame_small.shape[1]
            scale_y = orig_frame.shape[0] / frame_small.shape[0]
        else:
            scale_x = scale_y = 1.0

        result = []
        for i, (x, y, w, h) in enumerate(rects):
            # HOG confidence via weights
            if i < len(weights) and weights[i] < 0.5:  # filter weak
                continue
            startX = int(x * scale_x)
            startY = int(y * scale_y)
            endX = int((x + w) * scale_x)
            endY = int((y + h) * scale_y)
            result.append((startX, startY, endX, endY))

        return result


class YOLODetector(PersonDetector):
    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.4):
        super().__init__(confidence)
        if not HAS_YOLO:
            raise ImportError("ultralytics not installed")
        try:
            self.model = YOLO(model_path)
            logger.info(f"YOLO model loaded: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load YOLO: {e}")
            self.model = None

    def detect(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self.model is None:
            return []
        results = self.model(frame, verbose=False, conf=self.confidence, classes=[0])  # class 0 = person
        rects = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                rects.append((int(x1), int(y1), int(x2), int(y2)))
        return rects


def get_detector(detector_type: str = "auto", prototxt: Optional[str] = None, model: Optional[str] = None, confidence: float = 0.4) -> PersonDetector:
    """
    Factory to get best available detector
    Types: auto, mobilenet, hog, yolo
    """
    detector_type = detector_type.lower()

    if detector_type == "yolo":
        if HAS_YOLO:
            try:
                return YOLODetector(confidence=confidence)
            except Exception as e:
                logger.warning(f"YOLO failed, fallback: {e}")
        else:
            logger.warning("YOLO requested but ultralytics not installed, falling back")

    if detector_type in ("mobilenet", "auto"):
        det = MobileNetSSDetector(prototxt=prototxt, model=model, confidence=confidence)
        if det.is_loaded():
            return det
        if detector_type == "mobilenet":
            logger.warning("MobileNet requested but models not found, falling back to HOG")

    # Fallback to HOG - always works with OpenCV
    logger.info("Using HOG detector")
    return HOGDetector(confidence=confidence)
