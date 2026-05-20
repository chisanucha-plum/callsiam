"""OpenRouter LLM service for streaming chat completions."""

import json
import logging
from typing import Dict, Generator, List

import requests

from app.configuration import Configuration
from app.constants import LONG_API_TIMEOUT_SECONDS, SSE_DATA_PREFIX, SSE_DONE_MESSAGE

logger = logging.getLogger(__name__)

# Module-specific constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterLLM:
    """Client for OpenRouter LLM API with streaming support."""

    def __init__(self, config: Configuration) -> None:
        """Initialize OpenRouter LLM client.

        Args:
            config: Application configuration containing LLM settings.
        """
        self._config = config
        logger.info("OpenRouter LLM initialized with model: %s", config.llm.model)

    def stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """Stream chat completion responses from OpenRouter.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.

        Yields:
            Text chunks from the streaming response.
        """
        headers = self._build_headers()
        payload = self._build_payload(messages)

        try:
            with requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=LONG_API_TIMEOUT_SECONDS,
            ) as response:
                if response.status_code != 200:
                    logger.error(
                        "OpenRouter API error (status %d): %s",
                        response.status_code,
                        response.text
                    )
                    return

                yield from self._process_stream(response)

        except requests.exceptions.Timeout:
            logger.error("OpenRouter request timed out after %d seconds", LONG_API_TIMEOUT_SECONDS)
        except requests.exceptions.RequestException as exc:
            logger.error("OpenRouter request failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in LLM stream: %s", exc)

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for OpenRouter API request.

        Returns:
            Dictionary of HTTP headers.
        """
        return {
            "Authorization": f"Bearer {self._config.openrouter_api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: List[Dict[str, str]]) -> Dict:
        """Build request payload for OpenRouter API.

        Args:
            messages: List of message dictionaries.

        Returns:
            Dictionary containing the API request payload.
        """
        return {
            "model": self._config.llm.model,
            "messages": messages,
            "temperature": self._config.llm.temperature,
            "stream": True,
            "max_tokens": self._config.llm.max_tokens,
        }

    def _process_stream(self, response: requests.Response) -> Generator[str, None, None]:
        """Process Server-Sent Events stream from OpenRouter.

        Args:
            response: Streaming HTTP response.

        Yields:
            Text content from the stream.
        """
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode("utf-8")

            if not line_str.startswith(SSE_DATA_PREFIX):
                continue

            data_str = line_str[len(SSE_DATA_PREFIX):].strip()

            if data_str == SSE_DONE_MESSAGE:
                break

            content = self._extract_content(data_str)
            if content:
                yield content

    def _extract_content(self, data_str: str) -> str:
        """Extract content from SSE data string.

        Args:
            data_str: JSON string from SSE data field.

        Returns:
            Extracted content string or empty string if parsing fails.
        """
        try:
            chunk = json.loads(data_str)
            delta = chunk.get("choices", [{}])[0].get("delta", {})
            return delta.get("content", "")
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            logger.debug("Failed to parse stream chunk: %s", exc)
            return ""
