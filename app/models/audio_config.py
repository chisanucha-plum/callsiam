"""AudioConfig dataclass."""

from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio input/output configuration."""

    sample_rate: int = 16000
    frame_ms: int = 20
    min_audio_bytes: int = 6000
    output_sample_rate: int = 24000
    output_blocksize: int = 1024

    def frame_samples(self) -> int:
        """Calculate samples per frame."""
        return int(self.sample_rate * self.frame_ms / 1000)

    def frame_bytes(self) -> int:
        """Calculate bytes per frame (16-bit audio)."""
        return self.frame_samples() * 2
