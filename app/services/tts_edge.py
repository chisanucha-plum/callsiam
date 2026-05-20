"""Edge TTS service for text-to-speech conversion."""

import json
import logging
import re
from typing import Optional

import requests

from app.configuration import Configuration
from app.constants import DEFAULT_API_TIMEOUT_SECONDS, MIN_TEXT_LENGTH, THAI_CHAR_PATTERN

logger = logging.getLogger(__name__)

# Module-specific constants
RESPONSE_FORMAT = "mp3"

# Regex patterns for text cleaning
PATTERN_INVALID_CHARS = r"[^\u0000-\u007F\u0E00-\u0E7F\s.,!?]"
PATTERN_MULTIPLE_SPACES = r"\s+"


class EdgeTTS:
    """Client for Edge TTS API."""

    def __init__(self, config: Configuration) -> None:
        """Initialize Edge TTS client.

        Args:
            config: Application configuration containing TTS settings.
        """
        self._config = config
        logger.info("Edge TTS initialized with voice: %s", config.tts.voice)

    def fetch_mp3(self, text: str) -> Optional[bytes]:
        """Convert text to MP3 audio using Edge TTS API.

        Args:
            text: Text to convert to speech.

        Returns:
            MP3 audio data as bytes or None if conversion fails.
        """
        cleaned_text = self._clean_text(text)

        if not self._is_valid_text(cleaned_text):
            logger.debug("Text too short or empty after cleaning: '%s'", text)
            return None

        payload = self._build_payload(cleaned_text)

        try:
            response = requests.post(
                self._config.tts.url,
                headers=self._build_headers(),
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=DEFAULT_API_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                logger.error(
                    "TTS API error (status %d): %s",
                    response.status_code,
                    response.text
                )
                return None

            if not response.content:
                logger.warning("TTS API returned empty response")
                return None

            return response.content

        except requests.exceptions.Timeout:
            logger.error("TTS request timed out after %d seconds", DEFAULT_API_TIMEOUT_SECONDS)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("TTS request failed: %s", exc)
            return None
        except Exception as exc:
            logger.error("Unexpected error in TTS conversion: %s", exc)
            return None

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text for TTS processing.

        Removes invalid characters, fixes Thai spacing, and normalizes whitespace.

        Args:
            text: Input text to clean.

        Returns:
            Cleaned text.
        """
        # Remove invalid characters (keep ASCII, Thai, and basic punctuation)
        text = re.sub(PATTERN_INVALID_CHARS, "", text)

        # Remove spaces between Thai characters
        text = re.sub(THAI_CHAR_PATTERN, "", text)

        # Normalize multiple spaces to single space
        text = re.sub(PATTERN_MULTIPLE_SPACES, " ", text)

        return text.strip()

    @staticmethod
    def _is_valid_text(text: str) -> bool:
        """Check if text is valid for TTS conversion.

        Args:
            text: Text to validate.

        Returns:
            True if text is valid, False otherwise.
        """
        return bool(text and len(text.strip()) >= MIN_TEXT_LENGTH)

    def _build_headers(self) -> dict:
        """Build HTTP headers for TTS API request.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self._config.tts.key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, text: str) -> dict:
        """Build request payload for TTS API.

        Args:
            text: Text to convert to speech.

        Returns:
            Dictionary containing the API request payload.
        """
        return {
            "input": text,
            "voice": self._config.tts.voice,
            "response_format": RESPONSE_FORMAT,
            "speed": self._config.tts.speed,
        }
