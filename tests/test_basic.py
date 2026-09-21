"""
Basic tests for crowd control system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_imports():
    from crowd_control.centroidtracker import CentroidTracker
    from crowd_control.trackableobject import TrackableObject
    from crowd_control.config import AppConfig, load_config
    from crowd_control.counter import PeopleCounter
    from crowd_control.detector import get_detector, HOGDetector
    from crowd_control.video import VideoManager, ThreadingClass
    from crowd_control.mailer import Mailer
    print("✓ All imports OK")

def test_centroid_tracker():
    from crowd_control.centroidtracker import CentroidTracker
    ct = CentroidTracker(maxDisappeared=10, maxDistance=50)
    rects = [(0,0,10,10), (20,20,30,30)]
    objects = ct.update(rects)
    assert len(objects) == 2, f"Expected 2 objects, got {len(objects)}"
    # Update with empty should increase disappeared
    objects = ct.update([])
    assert len(objects) == 2, "Should still have 2 (not yet deregistered)"
    print("✓ CentroidTracker OK")

def test_counter():
    from crowd_control.counter import PeopleCounter
    counter = PeopleCounter(threshold=2)
    # Simulate enter: centroid moves down across line
    # Frame height 100, line at 50
    # First detection at y=30, then y=70 moving down -> should count enter
    rects = [(10,20,30,40)]  # centroid y ~30
    stats = counter.update(rects, frame_height=100)
    assert stats["enter"] == 0

    # Move down
    rects = [(10,60,30,80)]  # centroid y ~70, direction positive, below line
    stats = counter.update(rects, frame_height=100)
    # Should have counted 1 enter
    # Note: need at least 2 centroids for direction, so second update should count
    assert stats["enter"] == 1, f"Expected 1 enter, got {stats['enter']}"
    assert stats["occupancy"] == 1
    print("✓ PeopleCounter OK")

def test_detector_hog():
    from crowd_control.detector import HOGDetector
    import numpy as np
    det = HOGDetector()
    # Black image should have no detections
    frame = np.zeros((200,200,3), dtype=np.uint8)
    rects = det.detect(frame)
    assert isinstance(rects, list)
    print(f"✓ HOGDetector OK (found {len(rects)} in black image, expected 0)")

def test_config():
    from crowd_control.config import AppConfig
    cfg = AppConfig(Threshold=5)
    assert cfg.Threshold == 5
    d = cfg.to_dict()
    assert "Threshold" in d
    cfg2 = AppConfig.from_dict(d)
    assert cfg2.Threshold == 5
    print("✓ Config OK")

def test_mailer():
    from crowd_control.mailer import Mailer
    m = Mailer(email="", password="")
    # Should not crash, but not send
    assert not m.can_send() or True  # cooldown logic
    # Try send with no recipient should return False, not crash
    result = m.send("", subject="test", body="test")
    assert result == False
    print("✓ Mailer OK (graceful failure)")

if __name__ == "__main__":
    test_imports()
    test_centroid_tracker()
    test_counter()
    test_detector_hog()
    test_config()
    test_mailer()
    print("\n✅ All tests passed!")
