# Hosting guide

Real-time webcam apps have one catch: the camera is on the *visitor's* device, so video must reach your
code. You have three realistic options.

## Option A: Browser-only demo on GitHub Pages (free, best for a portfolio)
Run MediaPipe's JavaScript build in the visitor's browser. No server, no latency, video never leaves the
device, and hosting is free via **Settings → Pages**. Trade-off: it is a JS re-implementation, not this
Python code.

## Option B: Hugging Face Spaces with Docker (free, runs this repo as-is)
1. Create a Space at huggingface.co/new-space, choose **Docker**.
2. Clone the Space repo and copy this project into it.
3. Add this header to the **top of the Space's README.md** (not the GitHub one):
   ```
   ---
   title: Handtrack
   emoji: ✋
   sdk: docker
   app_port: 7860
   ---
   ```
4. `git push`. The Space builds the `Dockerfile` and serves the Streamlit app over HTTPS
   (required for browser camera access).

**WebRTC caveat:** behind some networks a STUN server is not enough and the video will not connect.
Add a TURN server (e.g. a free Twilio / Metered tier) to `rtc_configuration` in `streamlit_app.py`.

## Option C: Own VPS (full control)
```bash
docker build -t handtrack .
docker run -d -p 7860:7860 --restart unless-stopped handtrack
```
Put Caddy or Nginx in front for HTTPS (Caddy gets certificates automatically):
```
handtrack.yourdomain.com {
    reverse_proxy localhost:7860
}
```
Browsers only allow camera access on HTTPS (or localhost), so TLS is mandatory.

## Option D: Edge device
For an embedded demo, run the CLI directly on a Raspberry Pi with `--width 640 --height 480`.
