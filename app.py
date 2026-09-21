#!/usr/bin/env python3
"""
app.py - Web-only entry point
Starts just the web dashboard, useful for demo or when video processing runs separately

Usage:
    python app.py --port 5000
    # Then open http://localhost:5000
"""

import argparse
import logging
from crowd_control.webapp import create_app, app_state
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Crowd Control Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=5000, help="Port")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    # Create placeholder frame if no video
    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(placeholder, "Crowd Control System", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(placeholder, "Start main.py for live feed", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)
    cv2.putText(placeholder, f"Dashboard: http://{args.host}:{args.port}", (80, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100,255,100), 2)
    app_state.update_frame(placeholder)
    app_state.update_stats({
        "enter": 0,
        "exit": 0,
        "occupancy": 0,
        "threshold": 10,
        "alert": False,
        "fps": 0,
        "status": "Idle - Run main.py for counting"
    })

    app = create_app()
    print(f"""
╔════════════════════════════════════════════════╗
║  Crowd Control Dashboard                       ║
║  Running at http://{args.host}:{args.port}              ║
║                                                ║
║  For full system with counting:                ║
║  python main.py --web --web-port {args.port}            ║
╚════════════════════════════════════════════════╝
    """)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

if __name__ == "__main__":
    main()
