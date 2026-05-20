"""Shared schema configs (no secrets)."""

from dataclasses import dataclass


@dataclass
class VADConfig:
    padding_frames: int = 4
    max_silence_frames: int = 10
    rms_threshold: int = 180


@dataclass
class AudioConfig:
    sample_rate: int = 16000
    frame_ms: int = 20
    min_audio_bytes: int = 6000
    output_sample_rate: int = 24000
    output_blocksize: int = 1024

    def frame_samples(self) -> int:
        return int(self.sample_rate * self.frame_ms / 1000)

    def frame_bytes(self) -> int:
        return self.frame_samples() * 2


