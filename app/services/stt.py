"""Speech-to-Text service using Deepgram API."""

import logging
import re
from typing import Optional

from app.configuration import Configuration
from app.constants import THAI_CHAR_PATTERN
from app.services._core import get_http_pool

logger = logging.getLogger(__name__)

# Technical constants
AUDIO_ENCODING = "linear16"
AUDIO_CHANNELS = 1


class STTService:
    """Speech-to-Text using Deepgram API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize STT service.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._http = get_http_pool()
        logger.info(
            "STT initialized (model=%s, language=%s)",
            config.stt_model,
            config.stt_language,
        )

    def transcribe(self, pcm_bytes: bytes) -> str:
        """Transcribe PCM audio to text.

        Args:
            pcm_bytes: PCM audio data (linear16).

        Returns:
            Transcribed text or empty string on error.
        """
        if not pcm_bytes:
            logger.warning("Empty audio data")
            return ""

        url = self._build_url()
        headers = self._build_headers()

        try:
            response = self._http.post(
                url,
                headers=headers,
                data=pcm_bytes,
                timeout=self._config.api_timeouts.short,
            )

            if response.status_code != 200:
                logger.error("STT error: %d - %s", response.status_code, response.text)
                return ""

            transcript = self._extract_text(response.json())
            return self._clean_thai_text(transcript)

        except Exception as exc:
            logger.error("STT failed: %s", exc)
            return ""

    def _build_url(self) -> str:
        """Build API URL with parameters."""
        config = self._config
        punctuate = "true" if config.stt_punctuate else "false"

        return (
            f"{config.external_apis.deepgram_url}"
            f"?model={config.stt_model}"
            f"&language={config.stt_language}"
            f"&encoding={AUDIO_ENCODING}"
            f"&sample_rate={config.audio.sample_rate}"
            f"&channels={AUDIO_CHANNELS}"
            f"&punctuate={punctuate}"
        )

    def _build_headers(self) -> dict:
        """Build HTTP headers."""
        return {
            "Authorization": f"Token {self._config.deepgram_api_key}",
            "Content-Type": f"audio/l16; rate={self._config.audio.sample_rate}",
        }

    def _extract_text(self, response_data: dict) -> str:
        """Extract transcript from response."""
        try:
            return response_data["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Extract error: %s", exc)
            return ""

    @staticmethod
    def _clean_thai_text(text: str) -> str:
        """Remove spaces between Thai characters."""
        return re.sub(THAI_CHAR_PATTERN, "", text)
