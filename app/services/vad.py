import collections
import numpy as np

from app.configuration import Configuration


class VADSegmenter:
    def __init__(self, config: Configuration):
        self._frame_bytes = config.audio.frame_bytes()
        self._padding_frames = config.vad.padding_frames
        self._max_silence_frames = config.vad.max_silence_frames
        self._rms_threshold = config.vad.rms_threshold
        self._padding = collections.deque(maxlen=self._padding_frames)
        self.reset()

    def reset(self) -> None:
        self._triggered = False
        self._silence_frames = 0
        self._voiced_frames = []

    def _rms(self, frame_bytes: bytes) -> float:
        audio = np.frombuffer(frame_bytes, dtype=np.int16)
        return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))

    def process(self, frame_bytes: bytes):
        if len(frame_bytes) != self._frame_bytes:
            return None

        rms = self._rms(frame_bytes)
        is_speech = rms >= self._rms_threshold

        if not self._triggered:
            self._padding.append(frame_bytes)

            if is_speech:
                self._triggered = True
                self._voiced_frames.extend(self._padding)
                self._padding.clear()

            return None

        self._voiced_frames.append(frame_bytes)

        if is_speech:
            self._silence_frames = 0
            return None

        self._silence_frames += 1

        if self._silence_frames >= self._max_silence_frames:
            segment = b"".join(self._voiced_frames)
            self.reset()
            return segment

        return None
