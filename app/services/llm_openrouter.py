import json
import requests

from app.configuration import Configuration


class OpenRouterLLM:
    def __init__(self, config: Configuration):
        self._config = config

    def stream(self, messages):
        config = self._config
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {config.openrouter_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.llm.model,
            "messages": messages,
            "temperature": config.llm.temperature,
            "stream": True,
            "max_tokens": config.llm.max_tokens,
        }

        try:
            with requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=60,
            ) as response:
                if response.status_code != 200:
                    print("\nOpenRouter Error:")
                    print(response.text)
                    return

                for line in response.iter_lines():
                    if not line:
                        continue

                    line = line.decode("utf-8")

                    if not line.startswith("data:"):
                        continue

                    data_str = line[5:].strip()

                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                        delta = (
                            chunk["choices"][0]
                            ["delta"]
                            .get("content", "")
                        )

                        if delta:
                            yield delta

                    except Exception:
                        continue

        except Exception as exc:
            print(f"\nLLM Error: {exc}")
