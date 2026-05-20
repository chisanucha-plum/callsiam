"""Shared constants used across multiple modules.

This module contains constants that are used by multiple services or
have business logic significance across the application.
"""

# ============================================================================
# API Timeouts
# ============================================================================
DEFAULT_API_TIMEOUT_SECONDS = 30
LONG_API_TIMEOUT_SECONDS = 60
SHORT_API_TIMEOUT_SECONDS = 20

# ============================================================================
# Audio Constants (shared across services)
# ============================================================================
AUDIO_CHANNELS = 1
AUDIO_DTYPE = "int16"

# ============================================================================
# Text Processing
# ============================================================================
# Thai character range for text processing
THAI_CHAR_PATTERN = r"(?<=[ก-๙])\s(?=[ก-๙])"

# ============================================================================
# Business Logic
# ============================================================================
# Payment due day for call center bot
PAYMENT_DUE_DAY = 25

# Minimum text length for processing
MIN_TEXT_LENGTH = 2

# ============================================================================
# Server-Sent Events (SSE)
# ============================================================================
SSE_DATA_PREFIX = "data:"
SSE_DONE_MESSAGE = "[DONE]"
