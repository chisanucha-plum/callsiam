import re
import requests

from app.configuration import Configuration


class DeepgramSTT:
    def __init__(self, config: Configuration):
        self._config = config

    def transcribe(self, pcm_bytes: bytes) -> str:
        config = self._config
        url = (
            "https://api.deepgram.com/v1/listen"
            f"?model={config.stt_model}"
            f"&language={config.stt_language}"
            "&encoding=linear16"
            f"&sample_rate={config.audio.sample_rate}"
            "&channels=1"
            f"&punctuate={'true' if config.stt_punctuate else 'false'}"
        )

        headers = {
            "Authorization": f"Token {config.deepgram_api_key}",
            "Content-Type": f"audio/l16; rate={config.audio.sample_rate}",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                data=pcm_bytes,
                timeout=20,
            )

            if response.status_code != 200:
                print("\nDeepgram Error:")
                print(response.text)
                return ""

            data = response.json()

            transcript = (
                data["results"]["channels"][0]
                ["alternatives"][0]
                ["transcript"]
                .strip()
            )

            transcript = re.sub(
                r"(?<=[ก-๙])\s(?=[ก-๙])",
                "",
                transcript,
            )

            return transcript

        except Exception as exc:
            print(f"\nSTT Error: {exc}")
            return ""
