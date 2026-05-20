"""Voice Activity Detection (VAD) service for segmenting audio."""

import collections
import logging
from typing import List, Optional

import numpy as np

from app.configuration import Configuration

logger = logging.getLogger(__name__)


class VADSegmenter:
    """Voice Activity Detection segmenter using RMS energy threshold."""

    def __init__(self, config: Configuration) -> None:
        """Initialize VAD segmenter with configuration.

        Args:
            config: Application configuration containing VAD settings.
        """
        self._frame_bytes: int = config.audio.frame_bytes()
        self._padding_frames: int = config.vad.padding_frames
        self._max_silence_frames: int = config.vad.max_silence_frames
        self._rms_threshold: int = config.vad.rms_threshold
        self._padding: collections.deque = collections.deque(maxlen=self._padding_frames)
        
        self._triggered: bool = False
        self._silence_frames: int = 0
        self._voiced_frames: List[bytes] = []
        
        logger.info(
            "VAD initialized with RMS threshold: %d, max silence frames: %d",
            self._rms_threshold,
            self._max_silence_frames
        )

    def reset(self) -> None:
        """Reset VAD state to initial conditions."""
        self._triggered = False
        self._silence_frames = 0
        self._voiced_frames = []
        self._padding.clear()

    def process(self, frame_bytes: bytes) -> Optional[bytes]:
        """Process an audio frame and detect voice activity.

        Args:
            frame_bytes: Audio frame data as bytes.

        Returns:
            Complete audio segment when voice activity ends, None otherwise.
        """
        if len(frame_bytes) != self._frame_bytes:
            logger.warning(
                "Invalid frame size: expected %d, got %d",
                self._frame_bytes,
                len(frame_bytes)
            )
            return None

        rms = self._calculate_rms(frame_bytes)
        is_speech = rms >= self._rms_threshold

        if not self._triggered:
            return self._handle_pre_trigger(frame_bytes, is_speech)

        return self._handle_post_trigger(frame_bytes, is_speech)

    def _calculate_rms(self, frame_bytes: bytes) -> float:
        """Calculate Root Mean Square (RMS) energy of audio frame.

        Args:
            frame_bytes: Audio frame data.

        Returns:
            RMS energy value.
        """
        audio = np.frombuffer(frame_bytes, dtype=np.int16)
        return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))

    def _handle_pre_trigger(self, frame_bytes: bytes, is_speech: bool) -> Optional[bytes]:
        """Handle audio frame before voice activity is triggered.

        Args:
            frame_bytes: Audio frame data.
            is_speech: Whether speech is detected in this frame.

        Returns:
            None (no segment ready yet).
        """
        self._padding.append(frame_bytes)

        if is_speech:
            self._triggered = True
            self._voiced_frames.extend(self._padding)
            self._padding.clear()
            logger.debug("Voice activity triggered")

        return None

    def _handle_post_trigger(self, frame_bytes: bytes, is_speech: bool) -> Optional[bytes]:
        """Handle audio frame after voice activity is triggered.

        Args:
            frame_bytes: Audio frame data.
            is_speech: Whether speech is detected in this frame.

        Returns:
            Complete audio segment if silence threshold reached, None otherwise.
        """
        self._voiced_frames.append(frame_bytes)

        if is_speech:
            self._silence_frames = 0
            return None

        self._silence_frames += 1

        if self._silence_frames >= self._max_silence_frames:
            segment = b"".join(self._voiced_frames)
            logger.debug("Voice segment completed: %d bytes", len(segment))
            self.reset()
            return segment

        return None
