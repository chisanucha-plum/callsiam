"""Voice Activity Detection (VAD) service."""

import collections
import logging
from typing import List, Optional

import numpy as np

from app.configuration import Configuration

logger = logging.getLogger(__name__)


class VADService:
    """Detects voice activity in audio using RMS energy threshold."""

    def __init__(self, config: Configuration) -> None:
        """Initialize VAD service.

        Args:
            config: Application configuration.
        """
        self._frame_bytes = config.audio.frame_bytes()
        self._padding_frames = config.vad.padding_frames
        self._max_silence_frames = config.vad.max_silence_frames
        self._rms_threshold = config.vad.rms_threshold
        self._padding = collections.deque(maxlen=self._padding_frames)

        self._triggered = False
        self._silence_frames = 0
        self._voiced_frames: List[bytes] = []

        logger.info(
            "VAD initialized (threshold=%d, max_silence=%d)",
            self._rms_threshold,
            self._max_silence_frames,
        )

    def reset(self) -> None:
        """Reset VAD state."""
        self._triggered = False
        self._silence_frames = 0
        self._voiced_frames = []
        self._padding.clear()

    def process(self, frame_bytes: bytes) -> Optional[bytes]:
        """Process audio frame and detect voice activity.

        Args:
            frame_bytes: Audio frame data.

        Returns:
            Complete audio segment when voice ends, None otherwise.
        """
        if len(frame_bytes) != self._frame_bytes:
            logger.warning("Invalid frame size: %d", len(frame_bytes))
            return None

        rms = self._calculate_rms(frame_bytes)
        is_speech = rms >= self._rms_threshold

        if not self._triggered:
            return self._handle_pre_trigger(frame_bytes, is_speech)

        return self._handle_post_trigger(frame_bytes, is_speech)

    @staticmethod
    def _calculate_rms(frame_bytes: bytes) -> float:
        """Calculate RMS energy of audio frame."""
        audio = np.frombuffer(frame_bytes, dtype=np.int16)
        return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))

    def _handle_pre_trigger(self, frame_bytes: bytes, is_speech: bool) -> Optional[bytes]:
        """Handle frame before voice is detected."""
        self._padding.append(frame_bytes)

        if is_speech:
            self._triggered = True
            self._voiced_frames.extend(self._padding)
            self._padding.clear()
            logger.debug("Voice triggered")

        return None

    def _handle_post_trigger(self, frame_bytes: bytes, is_speech: bool) -> Optional[bytes]:
        """Handle frame after voice is detected."""
        self._voiced_frames.append(frame_bytes)

        if is_speech:
            self._silence_frames = 0
            return None

        self._silence_frames += 1

        if self._silence_frames >= self._max_silence_frames:
            segment = b"".join(self._voiced_frames)
            logger.debug("Segment completed: %d bytes", len(segment))
            self.reset()
            return segment

        return None
