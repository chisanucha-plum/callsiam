import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from app.schemas import AudioConfig, VADConfig


@dataclass
class TTS:
    url: str
    key: str
    voice: str
    speed: float

    @staticmethod
    def from_dict(obj: Any) -> "TTS":
        _url = str(obj.get("url", "http://localhost:5050/v1/audio/speech"))
        _key = str(obj.get("key", ""))
        _voice = str(obj.get("voice", "th-TH-PremwadeeNeural"))
        _speed = float(obj.get("speed", 1.18))
        return TTS(_url, _key, _voice, _speed)


@dataclass
class LLM:
    model: str
    temperature: float
    max_tokens: int

    @staticmethod
    def from_dict(obj: Any) -> "LLM":
        _model = str(obj.get("model", "openai/gpt-4o-mini"))
        _temperature = float(obj.get("temperature", 0.5))
        _max_tokens = int(obj.get("max_tokens", 80))
        return LLM(_model, _temperature, _max_tokens)


@dataclass
class Configuration:
    deepgram_api_key: str
    openrouter_api_key: str
    stt_model: str
    stt_language: str
    stt_punctuate: bool
    audio: AudioConfig
    vad: VADConfig
    tts: TTS
    llm: LLM

    @staticmethod
    def from_dict(obj: Any) -> "Configuration":
        _deepgram_api_key = str(
            obj.get("deepgram_api_key")
            or os.getenv("DEEPGRAM_API_KEY", "")
        )
        _openrouter_api_key = str(
            obj.get("openrouter_api_key")
            or os.getenv("OPENROUTER_API_KEY", "")
        )
        _stt_model = str(obj.get("stt_model", "nova-2"))
        _stt_language = str(obj.get("stt_language", "th"))
        _stt_punctuate = bool(obj.get("stt_punctuate", True))

        audio_obj = obj.get("audio", {})
        _audio = AudioConfig(
            sample_rate=int(audio_obj.get("sample_rate", 16000)),
            frame_ms=int(audio_obj.get("frame_ms", 20)),
            min_audio_bytes=int(audio_obj.get("min_audio_bytes", 6000)),
            output_sample_rate=int(
                audio_obj.get("output_sample_rate", 24000)
            ),
            output_blocksize=int(
                audio_obj.get("output_blocksize", 1024)
            ),
        )

        vad_obj = obj.get("vad", {})
        _vad = VADConfig(
            padding_frames=int(vad_obj.get("padding_frames", 4)),
            max_silence_frames=int(
                vad_obj.get("max_silence_frames", 10)
            ),
            rms_threshold=int(
                vad_obj.get("rms_threshold", 180)
            ),
        )
        tts_obj = obj.get("tts", {})
        if "key" not in tts_obj:
            tts_obj["key"] = os.getenv("EDGE_TTS_KEY", "")
        _tts = TTS.from_dict(tts_obj)
        _llm = LLM.from_dict(obj.get("llm", {}))

        return Configuration(
            _deepgram_api_key,
            _openrouter_api_key,
            _stt_model,
            _stt_language,
            _stt_punctuate,
            _audio,
            _vad,
            _tts,
            _llm,
        )

    @staticmethod
    @lru_cache
    def get_config() -> "Configuration":
        load_dotenv(".env")
        site = os.environ.get("SITE", "development")
        path = f"config.{site}.json"

        if os.path.exists(path):
            with open(path, encoding="utf-8") as file:
                config_json = json.load(file)
                config = Configuration.from_dict(config_json)
                return config

        return Configuration.from_dict({})

def load_config() -> Configuration:
    config = Configuration.get_config()

    if not config.deepgram_api_key:
        raise RuntimeError("Missing DEEPGRAM_API_KEY")

    if not config.openrouter_api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY")

    if not config.tts.key:
        raise RuntimeError("Missing EDGE_TTS_KEY")

    return config
