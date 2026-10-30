"""Rule-based gesture recognition from 21 MediaPipe hand landmarks.

Pure Python (no OpenCV / MediaPipe import), so it is fast to unit-test.
Finger state is measured by distance from the wrist, which makes it
independent of hand rotation.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Sequence, Tuple

Landmark = Tuple[float, float, float]

WRIST = 0
THUMB_IP, THUMB_TIP = 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20

# (pip, tip) pairs for index, middle, ring, pinky
_FINGERS = ((INDEX_PIP, INDEX_TIP), (MIDDLE_PIP, MIDDLE_TIP), (RING_PIP, RING_TIP), (PINKY_PIP, PINKY_TIP))


class Gesture(str, Enum):
    OPEN_PALM = "OPEN_PALM"
    FIST = "FIST"
    POINTING = "POINTING"
    PEACE = "PEACE"
    THUMBS_UP = "THUMBS_UP"
    ROCK = "ROCK"
    OK = "OK"
    UNKNOWN = "UNKNOWN"


def _dist(a: Landmark, b: Landmark) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def fingers_up(lm: Sequence[Landmark]) -> Tuple[bool, bool, bool, bool, bool]:
    """Return (thumb, index, middle, ring, pinky) extended flags."""
    if len(lm) != 21:
        raise ValueError(f"Expected 21 landmarks, got {len(lm)}")
    wrist = lm[WRIST]
    thumb = _dist(lm[THUMB_TIP], lm[PINKY_MCP]) > _dist(lm[THUMB_IP], lm[PINKY_MCP])
    others = tuple(_dist(lm[tip], wrist) > _dist(lm[pip], wrist) for pip, tip in _FINGERS)
    return (thumb, *others)  # type: ignore[return-value]


def classify(lm: Sequence[Landmark]) -> Gesture:
    """Classify a single hand into a Gesture."""
    thumb, index, middle, ring, pinky = fingers_up(lm)

    hand_size = max(_dist(lm[WRIST], lm[MIDDLE_MCP]), 1e-6)
    pinch = _dist(lm[THUMB_TIP], lm[INDEX_TIP]) / hand_size
    if pinch < 0.25 and middle and ring and pinky:
        return Gesture.OK

    if index and middle and ring and pinky:
        return Gesture.OPEN_PALM
    if index and middle and not ring and not pinky:
        return Gesture.PEACE
    if index and pinky and not middle and not ring:
        return Gesture.ROCK
    if index and not middle and not ring and not pinky:
        return Gesture.POINTING
    if not (index or middle or ring or pinky):
        if thumb and lm[THUMB_TIP][1] < lm[INDEX_MCP][1]:  # thumb pointing up (y grows downward)
            return Gesture.THUMBS_UP
        if not thumb:
            return Gesture.FIST
    return Gesture.UNKNOWN
