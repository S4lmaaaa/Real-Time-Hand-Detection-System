"""Command-line entry point: webcam / video file hand detection."""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import List, Optional

import cv2

from .gestures import classify
from .utils import FPSCounter


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="handtrack", description="Real-time hand detection & gesture recognition.")
    p.add_argument("--camera", type=int, default=0, help="Webcam index (default: 0)")
    p.add_argument("--video", type=str, default=None, help="Path to a video file instead of a webcam")
    p.add_argument("--output", type=str, default=None, help="Write the annotated video to this path (.mp4)")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--max-hands", type=int, default=2)
    p.add_argument("--detection-conf", type=float, default=0.6)
    p.add_argument("--tracking-conf", type=float, default=0.5)
    p.add_argument("--no-gestures", action="store_true", help="Disable gesture classification")
    p.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=None,
                   help="Mirror the frame (default: on for webcam, off for video files)")
    p.add_argument("--headless", action="store_true", help="No window (useful with --video/--output)")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    from .detector import HandDetector, draw_hands  # lazy: keeps --help fast

    mirror = args.mirror if args.mirror is not None else args.video is None
    cap = cv2.VideoCapture(args.video if args.video else args.camera)
    if not cap.isOpened():
        print("Error: could not open the video source.", file=sys.stderr)
        return 1
    if not args.video:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    writer = None
    fps_counter = FPSCounter()
    try:
        with HandDetector(args.max_hands, args.detection_conf, args.tracking_conf) as det:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if mirror:
                    frame = cv2.flip(frame, 1)

                hands = det.process(frame)
                gestures = None if args.no_gestures else [classify(h.landmarks) for h in hands]
                draw_hands(frame, hands, gestures)

                fps = fps_counter.tick()
                cv2.putText(frame, f"FPS: {fps:.1f}  Hands: {len(hands)}", (10, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)

                if args.output:
                    if writer is None:
                        h, w = frame.shape[:2]
                        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                        writer = cv2.VideoWriter(args.output, cv2.VideoWriter_fourcc(*"mp4v"), src_fps, (w, h))
                    writer.write(frame)

                if not args.headless:
                    cv2.imshow("handtrack  (q: quit, s: screenshot)", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    if key == ord("s"):
                        os.makedirs("screenshots", exist_ok=True)
                        path = os.path.join("screenshots", f"hand_{int(time.time())}.png")
                        cv2.imwrite(path, frame)
                        print(f"Saved {path}")
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
