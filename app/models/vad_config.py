"""VADConfig dataclass."""

from dataclasses import dataclass


@dataclass
class VADConfig:
    """Voice Activity Detection configuration."""

    padding_frames: int = 4
    max_silence_frames: int = 10
    rms_threshold: int = 180
