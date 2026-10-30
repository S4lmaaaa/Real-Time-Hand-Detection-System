"""MediaPipe HandLandmarker (Tasks API) wrapper that returns plain Python objects."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from .gestures import Gesture, Landmark

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
DEFAULT_MODEL_PATH = Path.home() / ".cache" / "handtrack" / "hand_landmarker.task"

# Skeleton of the 21-point hand model (pairs of landmark indices).
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),            # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),            # index
    (5, 9), (9, 10), (10, 11), (11, 12),       # middle
    (9, 13), (13, 14), (14, 15), (15, 16),     # ring
    (13, 17), (17, 18), (18, 19), (19, 20),    # pinky
    (0, 17),                                    # palm edge
)


def ensure_model(path: Path = DEFAULT_MODEL_PATH) -> Path:
    """Return the path to the hand landmarker model, downloading it (~8 MB) on first use."""
    path = Path(path)
    if path.exists() and path.stat().st_size > 0:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading hand landmarker model to {path} ...")
    tmp = path.with_suffix(".part")
    try:
        urllib.request.urlretrieve(MODEL_URL, tmp)
    except (urllib.error.URLError, OSError) as exc:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"Could not download the model ({exc}).\n"
            f"Download it manually from:\n  {MODEL_URL}\nand save it as:\n  {path}"
        ) from exc
    tmp.replace(path)
    return path


@dataclass
class Hand:
    """One detected hand. Landmark coordinates are normalized to [0, 1]."""

    label: str  # "Left" or "Right" (from the user's view when the frame is mirrored)
    score: float
    landmarks: list[Landmark]

    def pixel_points(self, width: int, height: int) -> list[tuple[int, int]]:
        return [(int(x * width), int(y * height)) for x, y, _ in self.landmarks]

    def bbox(self, width: int, height: int, pad: int = 20) -> tuple[int, int, int, int]:
        pts = self.pixel_points(width, height)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (max(min(xs) - pad, 0), max(min(ys) - pad, 0),
                min(max(xs) + pad, width - 1), min(max(ys) + pad, height - 1))


class HandDetector:
    """Real-time hand detector. Use as a context manager to release resources."""

    def __init__(self, max_hands: int = 2, detection_conf: float = 0.6,
                 tracking_conf: float = 0.5, model_path: str | Path | None = None) -> None:
        model = ensure_model(Path(model_path) if model_path else DEFAULT_MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_conf,
            min_hand_presence_confidence=tracking_conf,
            min_tracking_confidence=tracking_conf,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._t0 = time.monotonic()
        self._last_ts = -1

    def _timestamp_ms(self) -> int:
        ts = int((time.monotonic() - self._t0) * 1000)
        if ts <= self._last_ts:  # VIDEO mode requires strictly increasing timestamps
            ts = self._last_ts + 1
        self._last_ts = ts
        return ts

    def process(self, frame_bgr) -> list[Hand]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(image, self._timestamp_ms())
        hands: list[Hand] = []
        for lms, handed in zip(result.hand_landmarks, result.handedness):
            cat = handed[0]
            hands.append(Hand(cat.category_name, float(cat.score),
                              [(p.x, p.y, p.z) for p in lms]))
        return hands

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> HandDetector:
        return self

    def __exit__(self, *exc) -> None:
        self.close()


def draw_hands(frame, hands: Sequence[Hand], gestures: Sequence[Gesture] | None = None) -> None:
    """Draw skeletons, bounding boxes and labels onto `frame` in place."""
    h, w = frame.shape[:2]
    for i, hand in enumerate(hands):
        pts = hand.pixel_points(w, h)
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 220, 0), 2, cv2.LINE_AA)
        for p in pts:
            cv2.circle(frame, p, 4, (0, 0, 255), -1, cv2.LINE_AA)
        x1, y1, x2, y2 = hand.bbox(w, h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 160, 0), 2)
        label = f"{hand.label} {hand.score:.0%}"
        if gestures is not None:
            label += f" | {gestures[i].value}"
        cv2.putText(frame, label, (x1, max(y1 - 8, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 160, 0), 2, cv2.LINE_AA)
