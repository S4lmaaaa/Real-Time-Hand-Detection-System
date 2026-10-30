import pytest

from handtrack.gestures import Gesture, classify, fingers_up

MCP = {"index": (0.45, 0.60), "middle": (0.50, 0.58), "ring": (0.55, 0.60), "pinky": (0.60, 0.65)}
BASE_IDX = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}


def make_hand(index=True, middle=True, ring=True, pinky=True, thumb="out"):
    """Synthetic upright right hand. thumb: 'out' | 'up' | 'folded'."""
    lm = [(0.5, 0.9, 0.0)] * 21
    lm = list(lm)
    thumbs = {
        "out": [(0.42, 0.82), (0.37, 0.74), (0.32, 0.68), (0.27, 0.62)],
        "up": [(0.45, 0.85), (0.42, 0.75), (0.40, 0.65), (0.39, 0.55)],
        "folded": [(0.45, 0.82), (0.43, 0.76), (0.40, 0.70), (0.47, 0.68)],
    }[thumb]
    for i, (x, y) in enumerate(thumbs, start=1):
        lm[i] = (x, y, 0.0)
    for name, up in (("index", index), ("middle", middle), ("ring", ring), ("pinky", pinky)):
        x, y = MCP[name]
        b = BASE_IDX[name]
        if up:
            ys = (y, y - 0.08, y - 0.14, y - 0.20)
            xs = (x, x, x, x)
        else:
            ys = (y, y - 0.06, y - 0.02, y + 0.04)
            xs = (x, x, x + 0.01, x + 0.02)
        for k in range(4):
            lm[b + k] = (xs[k], ys[k], 0.0)
    return lm


def test_requires_21_landmarks():
    with pytest.raises(ValueError):
        fingers_up([(0, 0, 0)] * 5)


def test_fingers_up_open():
    assert fingers_up(make_hand()) == (True, True, True, True, True)


def test_fingers_up_fist():
    assert fingers_up(make_hand(False, False, False, False, thumb="folded")) == (False,) * 5


def test_open_palm():
    assert classify(make_hand()) is Gesture.OPEN_PALM


def test_fist():
    assert classify(make_hand(False, False, False, False, thumb="folded")) is Gesture.FIST


def test_pointing():
    assert classify(make_hand(True, False, False, False, thumb="folded")) is Gesture.POINTING


def test_peace():
    assert classify(make_hand(True, True, False, False, thumb="folded")) is Gesture.PEACE


def test_rock():
    assert classify(make_hand(True, False, False, True, thumb="folded")) is Gesture.ROCK


def test_thumbs_up():
    assert classify(make_hand(False, False, False, False, thumb="up")) is Gesture.THUMBS_UP


def test_ok_sign():
    lm = make_hand(True, True, True, True)
    lm[4] = (lm[8][0] + 0.01, lm[8][1] + 0.01, 0.0)  # thumb tip touches index tip
    assert classify(lm) is Gesture.OK


def test_rotation_invariance():
    """Rotate an open palm 90 degrees; it must still be an open palm."""
    rotated = [(1 - y, x, z) for x, y, z in make_hand()]
    assert classify(rotated) is Gesture.OPEN_PALM
