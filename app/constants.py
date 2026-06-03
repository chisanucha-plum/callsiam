"""Shared technical constants used across multiple modules.

This module contains only technical constants that should NOT be configurable
(e.g., data types, encoding formats). Business logic values and tuneable
parameters belong in configuration files.
"""

# ============================================================================
# Audio Technical Constants (not configurable)
# ============================================================================
AUDIO_CHANNELS: int = 1
AUDIO_DTYPE: str = "int16"

# ============================================================================
# Text Processing Patterns
# ============================================================================
# Thai character range for text processing (Unicode range - technical constant)
THAI_CHAR_PATTERN: str = r"(?<=[ก-๙])\s(?=[ก-๙])"

# ============================================================================
# Server-Sent Events (SSE) Protocol Constants
# ============================================================================
SSE_DATA_PREFIX: str = "data:"
SSE_DONE_MESSAGE: str = "[DONE]"
