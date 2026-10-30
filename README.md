# ✋ handtrack

Real-time hand detection, 21-point landmark tracking and gesture recognition using **MediaPipe** and **OpenCV**.
Runs from the command line (webcam or video file) or as a browser demo with Streamlit.

[![CI](https://github.com/YOUR_USERNAME/handtrack/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/handtrack/actions)
![Python](https://img.shields.io/badge/python-3.10--3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)

<!-- Replace with a 5-10 second GIF of your demo: -->
<!-- ![demo](docs/assets/demo.gif) -->

## Features
- Detects up to N hands in real time (CPU only)
- 21 landmarks per hand, skeleton overlay, bounding box, Left/Right label and confidence
- Rotation-invariant gesture recognition: open palm, fist, pointing, peace, thumbs up, rock, OK
- Webcam, video-file input, annotated video export, screenshot hotkey
- Browser demo (Streamlit + WebRTC) and Dockerfile
- Unit-tested gesture logic and CI

## Quick start
```bash
git clone https://github.com/YOUR_USERNAME/handtrack.git
cd handtrack
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m handtrack
```
On first run the ~8 MB hand landmarker model is downloaded to `~/.cache/handtrack/` automatically.
Press `q` to quit and `s` to save a screenshot.

> **Windows tip:** if `Activate.ps1` is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
> Don't use `source`, it only exists in Linux/macOS shells.

## Usage
```bash
python -m handtrack --camera 1 --max-hands 1          # another webcam, one hand
python -m handtrack --video input.mp4 --output out.mp4 --headless
python -m handtrack --no-gestures                     # landmarks only
```
| Flag | Default | Description |
|---|---|---|
| `--camera` | 0 | Webcam index |
| `--video` | none | Video file instead of webcam |
| `--output` | none | Save annotated video |
| `--max-hands` | 2 | Maximum hands to track |
| `--detection-conf` | 0.6 | Minimum detection confidence |
| `--tracking-conf` | 0.5 | Minimum tracking confidence |
| `--mirror / --no-mirror` | auto | Mirror frames (on for webcam) |
| `--headless` | off | No window |

### Browser demo
```bash
pip install -r requirements-web.txt
streamlit run streamlit_app.py
```

### As a library
```python
import cv2
from handtrack.detector import HandDetector
from handtrack.gestures import classify

with HandDetector(max_hands=2) as det:
    frame = cv2.imread("hand.jpg")
    for hand in det.process(frame):
        print(hand.label, classify(hand.landmarks))
```

## How it works
1. **Detection:** MediaPipe's HandLandmarker (Tasks API) locates palms, then regresses 21 3D keypoints.
   In video mode it tracks between frames instead of re-detecting, which is what makes it fast.
2. **Gestures:** A finger counts as extended when its tip is farther from the wrist than its middle joint
   (the thumb is measured against the pinky base). Because only distances are used, gestures work at any hand
   rotation. Rules map finger states to gestures; the OK sign uses the thumb-index pinch distance.
3. **Rendering:** OpenCV draws the skeleton, box and label. Frames are mirrored first so Left/Right labels
   match what the user sees.

## Project structure
```
handtrack/
├── handtrack/
│   ├── detector.py    # MediaPipe wrapper + drawing
│   ├── gestures.py    # landmark → gesture rules (dependency-free)
│   ├── app.py         # CLI
│   └── utils.py       # FPS counter
├── streamlit_app.py   # browser demo
├── tests/             # pytest suite
├── docs/DEPLOYMENT.md # hosting guide
├── Dockerfile
└── .github/workflows/ci.yml
```

## Performance tips
- Lower the resolution (`--width 640 --height 480`) on weak hardware.
- Good, even lighting matters more than any parameter.
- Fewer `--max-hands` means less work per frame.

## Limitations
- Gestures are heuristic rules, not a trained classifier; unusual angles can misclassify.
- Heavy occlusion or fast motion blur lowers landmark accuracy.

## Roadmap
- [ ] Trained gesture classifier on landmark vectors
- [ ] Custom gesture recording
- [ ] Raspberry Pi / edge benchmarks
- [ ] Gesture-controlled actions (volume, slides)

## Hosting
See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## License
MIT, see [LICENSE](LICENSE). Built on [MediaPipe](https://github.com/google-ai-edge/mediapipe) (Apache 2.0).
