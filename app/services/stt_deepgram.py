"""Deepgram Speech-to-Text service."""

import logging
import re
from typing import Optional

import requests

from app.configuration import Configuration
from app.constants import SHORT_API_TIMEOUT_SECONDS, THAI_CHAR_PATTERN

logger = logging.getLogger(__name__)

# Module-specific constants
DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"
AUDIO_ENCODING = "linear16"
AUDIO_CHANNELS = 1


class DeepgramSTT:
    """Client for Deepgram Speech-to-Text API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize Deepgram STT client.

        Args:
            config: Application configuration containing STT settings.
        """
        self._config = config
        logger.info(
            "Deepgram STT initialized with model: %s, language: %s",
            config.stt_model,
            config.stt_language
        )

    def transcribe(self, pcm_bytes: bytes) -> str:
        """Transcribe PCM audio to text using Deepgram API.

        Args:
            pcm_bytes: PCM audio data in linear16 format.

        Returns:
            Transcribed text or empty string if transcription fails.
        """
        if not pcm_bytes:
            logger.warning("Empty audio data provided for transcription")
            return ""

        url = self._build_api_url()
        headers = self._build_headers()

        try:
            response = requests.post(
                url,
                headers=headers,
                data=pcm_bytes,
                timeout=SHORT_API_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                logger.error(
                    "Deepgram API error (status %d): %s",
                    response.status_code,
                    response.text
                )
                return ""

            transcript = self._extract_transcript(response.json())
            return self._clean_thai_text(transcript)

        except requests.exceptions.Timeout:
            logger.error("Deepgram request timed out after %d seconds", SHORT_API_TIMEOUT_SECONDS)
            return ""
        except requests.exceptions.RequestException as exc:
            logger.error("Deepgram request failed: %s", exc)
            return ""
        except Exception as exc:
            logger.error("Unexpected error in STT transcription: %s", exc)
            return ""

    def _build_api_url(self) -> str:
        """Build Deepgram API URL with query parameters.

        Returns:
            Complete API URL with parameters.
        """
        config = self._config
        punctuate_str = "true" if config.stt_punctuate else "false"
        
        return (
            f"{DEEPGRAM_API_URL}"
            f"?model={config.stt_model}"
            f"&language={config.stt_language}"
            f"&encoding={AUDIO_ENCODING}"
            f"&sample_rate={config.audio.sample_rate}"
            f"&channels={AUDIO_CHANNELS}"
            f"&punctuate={punctuate_str}"
        )

    def _build_headers(self) -> dict:
        """Build HTTP headers for Deepgram API request.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Token {self._config.deepgram_api_key}",
            "Content-Type": f"audio/l16; rate={self._config.audio.sample_rate}",
        }

    def _extract_transcript(self, response_data: dict) -> str:
        """Extract transcript text from Deepgram API response.

        Args:
            response_data: JSON response from Deepgram API.

        Returns:
            Extracted transcript text.
        """
        try:
            transcript = (
                response_data["results"]["channels"][0]
                ["alternatives"][0]["transcript"]
            )
            return transcript.strip()
        except (KeyError, IndexError) as exc:
            logger.error("Failed to extract transcript from response: %s", exc)
            return ""

    def _clean_thai_text(self, text: str) -> str:
        """Remove unnecessary spaces between Thai characters.

        Args:
            text: Input text to clean.

        Returns:
            Cleaned text with Thai character spacing fixed.
        """
        return re.sub(THAI_CHAR_PATTERN, "", text)
