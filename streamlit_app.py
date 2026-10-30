"""Browser demo: run with `streamlit run streamlit_app.py`."""

import av
import cv2
import streamlit as st
from streamlit_webrtc import RTCConfiguration, webrtc_streamer

from handtrack.detector import HandDetector, draw_hands
from handtrack.gestures import classify

st.set_page_config(page_title="handtrack", page_icon="✋")
st.title("✋ Real-time hand detection")
st.caption("MediaPipe Hands + OpenCV. Video is processed live; nothing is stored.")

max_hands = st.sidebar.slider("Max hands", 1, 4, 2)
show_gestures = st.sidebar.checkbox("Recognize gestures", value=True)


class Processor:
    def __init__(self) -> None:
        self.detector = HandDetector(max_hands=max_hands)
        self.show_gestures = show_gestures

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = cv2.flip(frame.to_ndarray(format="bgr24"), 1)
        hands = self.detector.process(img)
        gestures = [classify(h.landmarks) for h in hands] if self.show_gestures else None
        draw_hands(img, hands, gestures)
        return av.VideoFrame.from_ndarray(img, format="bgr24")


webrtc_streamer(
    key="handtrack",
    video_processor_factory=Processor,
    rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)
