"""Text-to-Speech service using Edge TTS API with caching."""

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from app.configuration import Configuration
from app.constants import THAI_CHAR_PATTERN
from app.services._core import ResponseCache, get_http_pool, make_cache_key

logger = logging.getLogger(__name__)

# Technical constants
RESPONSE_FORMAT = "mp3"
PATTERN_INVALID_CHARS = r"[^\u0000-\u007F\u0E00-\u0E7F\s.,!?]"
PATTERN_MULTIPLE_SPACES = r"\s+"

# Common Thai phrases for preloading
COMMON_PHRASES = [
    "สวัสดีครับ",
    "สวัสดีค่ะ",
    "ขอบคุณครับ",
    "ขอบคุณค่ะ",
    "เข้าใจแล้วครับ",
    "เข้าใจแล้วค่ะ",
    "ได้เลยครับ",
    "ได้เลยค่ะ",
]


class TTSService:
    """Text-to-Speech service with response caching."""

    def __init__(self, config: Configuration) -> None:
        """Initialize TTS service.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._http = get_http_pool()
        self._cache = ResponseCache(max_size=100)
        self._min_length = config.text_processing.min_text_length
        self._executor = ThreadPoolExecutor(max_workers=3)

        # Preload common phrases
        self._preload_common_phrases()
        logger.info("TTS initialized (voice=%s, cache_enabled=true)", config.tts.voice)

    def fetch_mp3(self, text: str) -> Optional[bytes]:
        """Convert text to MP3.

        Args:
            text: Text to synthesize.

        Returns:
            MP3 bytes or None on error.
        """
        cleaned = self._clean_text(text)

        if not self._is_valid_text(cleaned):
            return None

        # Check cache first
        cache_key = make_cache_key(cleaned)
        cached = self._cache.get(cache_key)
        if cached:
            logger.debug("TTS cache hit: %s", text[:30])
            return cached

        # Generate new
        mp3_data = self._generate(cleaned)

        # Store in cache
        if mp3_data:
            self._cache.put(cache_key, mp3_data)

        return mp3_data

    def fetch_batch(self, texts: List[str]) -> List[Tuple[str, Optional[bytes]]]:
        """Process multiple texts in parallel.

        Args:
            texts: List of texts to synthesize.

        Returns:
            List of (text, mp3_bytes) tuples.
        """
        futures = {
            self._executor.submit(self.fetch_mp3, text): text
            for text in texts
        }

        results = []
        for future in as_completed(futures):
            text = futures[future]
            try:
                mp3_data = future.result()
                results.append((text, mp3_data))
            except Exception as exc:
                logger.error("Batch TTS failed for '%s': %s", text, exc)
                results.append((text, None))

        return results

    def close(self) -> None:
        """Shutdown service."""
        self._executor.shutdown(wait=True)
        logger.info("TTS service closed")

    def _generate(self, text: str) -> Optional[bytes]:
        """Call TTS API to generate MP3."""
        payload = self._build_payload(text)

        try:
            response = self._http.post(
                self._config.tts.url,
                headers=self._build_headers(),
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                timeout=self._config.api_timeouts.default,
            )

            if response.status_code != 200:
                logger.error("TTS error: %d", response.status_code)
                return None

            return response.content if response.content else None

        except Exception as exc:
            logger.error("TTS generation failed: %s", exc)
            return None

    def _preload_common_phrases(self) -> None:
        """Preload cache with common phrases."""
        logger.debug("Preloading %d common phrases", len(COMMON_PHRASES))
        for phrase in COMMON_PHRASES:
            cache_key = make_cache_key(phrase)
            if self._cache.get(cache_key) is None:
                mp3_data = self._generate(phrase)
                if mp3_data:
                    self._cache.put(cache_key, mp3_data)

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(PATTERN_INVALID_CHARS, "", text)
        text = re.sub(THAI_CHAR_PATTERN, "", text)
        text = re.sub(PATTERN_MULTIPLE_SPACES, " ", text)
        return text.strip()

    def _is_valid_text(self, text: str) -> bool:
        """Check if text is valid."""
        return bool(text and len(text) >= self._min_length)

    def _build_headers(self) -> dict:
        """Build HTTP headers."""
        return {
            "Authorization": f"Bearer {self._config.tts.key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, text: str) -> dict:
        """Build request payload."""
        return {
            "input": text,
            "voice": self._config.tts.voice,
            "response_format": RESPONSE_FORMAT,
            "speed": self._config.tts.speed,
        }
