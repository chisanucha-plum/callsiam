"""Voice bot application package.

A production-focused Thai call center voice bot with:
- Realtime audio capture with Voice Activity Detection
- Deepgram Speech-to-Text (Thai language support)
- OpenRouter LLM streaming
- Edge TTS playback
"""

__version__ = "1.0.0"
__author__ = "CallSiam Team"

__all__ = ["configuration", "constants", "controllers", "models", "services"]
