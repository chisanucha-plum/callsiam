"""Large Language Model service using OpenRouter API."""

import json
import logging
from typing import Dict, Generator, List

from app.configuration import Configuration
from app.constants import SSE_DATA_PREFIX, SSE_DONE_MESSAGE
from app.services._core import get_http_pool

logger = logging.getLogger(__name__)

# API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMService:
    """LLM service with streaming support via OpenRouter."""

    def __init__(self, config: Configuration) -> None:
        """Initialize LLM service.

        Args:
            config: Application configuration.
        """
        self._config = config
        self._http = get_http_pool()
        logger.info("LLM initialized (model=%s)", config.llm.model)

    def stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream LLM response.

        Args:
            messages: Chat history.

        Yields:
            Response text chunks.
        """
        headers = self._build_headers()
        payload = self._build_payload(messages)

        try:
            response = self._http.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=self._config.api_timeouts.long,
            )

            if response.status_code != 200:
                logger.error("LLM error: %d", response.status_code)
                return

            # Use raw requests.Response for streaming
            yield from self._process_stream(response)

        except Exception as exc:
            logger.error("LLM stream failed: %s", exc)

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers."""
        return {
            "Authorization": f"Bearer {self._config.openrouter_api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: List[Dict[str, str]]) -> Dict:
        """Build request payload."""
        return {
            "model": self._config.llm.model,
            "messages": messages,
            "temperature": self._config.llm.temperature,
            "stream": True,
            "max_tokens": self._config.llm.max_tokens,
        }

    @staticmethod
    def _process_stream(response) -> Generator[str, None, None]:
        """Process SSE stream."""
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode("utf-8")

            if not line_str.startswith(SSE_DATA_PREFIX):
                continue

            data_str = line_str[len(SSE_DATA_PREFIX):].strip()

            if data_str == SSE_DONE_MESSAGE:
                break

            content = LLMService._extract_content(data_str)
            if content:
                yield content

    @staticmethod
    def _extract_content(data_str: str) -> str:
        """Extract content from SSE data."""
        try:
            chunk = json.loads(data_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            return delta.get("content", "")
        except Exception:
            return ""
