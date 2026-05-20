import json
import re
import requests

from app.configuration import Configuration


class EdgeTTS:
    def __init__(self, config: Configuration):
        self._config = config

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(
            r"[^\u0000-\u007F\u0E00-\u0E7F\s.,!?]",
            "",
            text,
        )

        text = re.sub(
            r"(?<=[ก-๙])\s(?=[ก-๙])",
            "",
            text,
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def fetch_mp3(self, text: str):
        config = self._config
        text = self.clean_text(text)

        if not text:
            return None

        if len(text.strip()) <= 1:
            return None

        payload = {
            "input": text,
            "voice": config.tts.voice,
            "response_format": "mp3",
            "speed": config.tts.speed,
        }

        try:
            response = requests.post(
                config.tts.url,
                headers={
                    "Authorization": f"Bearer {config.tts.key}",
                    "Content-Type": "application/json",
                },
                data=json.dumps(
                    payload,
                    ensure_ascii=False,
                ).encode("utf-8"),
                timeout=30,
            )

            if response.status_code != 200:
                print("\nTTS Error:")
                print(response.text)
                return None

            if not response.content:
                return None

            return response.content

        except Exception as exc:
            print(f"\nTTS Exception: {exc}")
            return None
