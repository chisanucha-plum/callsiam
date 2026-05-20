"""Shared schema configurations for audio and VAD settings."""

from dataclasses import dataclass


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""

    padding_frames: int = 4
    max_silence_frames: int = 10
    rms_threshold: int = 180


@dataclass
class AudioConfig:
    """Audio processing configuration."""

    sample_rate: int = 16000
    frame_ms: int = 20
    min_audio_bytes: int = 6000
    output_sample_rate: int = 24000
    output_blocksize: int = 1024

    def frame_samples(self) -> int:
        """Calculate number of samples per frame.

        Returns:
            Number of samples in one frame.
        """
        return int(self.sample_rate * self.frame_ms / 1000)

    def frame_bytes(self) -> int:
        """Calculate number of bytes per frame (16-bit audio).

        Returns:
            Number of bytes in one frame.
        """
        return self.frame_samples() * 2


