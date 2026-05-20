"""Configuration management for the voice bot application."""

import json
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

from dotenv import load_dotenv

from app.schemas import AudioConfig, VADConfig

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_SITE = "development"
CONFIG_FILE_TEMPLATE = "config.{site}.json"


@dataclass
class TTS:
    """Text-to-Speech configuration."""

    url: str
    key: str
    voice: str
    speed: float

    @staticmethod
    def from_dict(obj: Any) -> "TTS":
        """Create TTS config from dictionary.

        Args:
            obj: Dictionary containing TTS configuration.

        Returns:
            TTS configuration instance.
        """
        return TTS(
            url=str(obj.get("url", "http://localhost:5050/v1/audio/speech")),
            key=str(obj.get("key", "")),
            voice=str(obj.get("voice", "th-TH-PremwadeeNeural")),
            speed=float(obj.get("speed", 1.18)),
        )


@dataclass
class LLM:
    """Large Language Model configuration."""

    model: str
    temperature: float
    max_tokens: int

    @staticmethod
    def from_dict(obj: Any) -> "LLM":
        """Create LLM config from dictionary.

        Args:
            obj: Dictionary containing LLM configuration.

        Returns:
            LLM configuration instance.
        """
        return LLM(
            model=str(obj.get("model", "openai/gpt-4o-mini")),
            temperature=float(obj.get("temperature", 0.5)),
            max_tokens=int(obj.get("max_tokens", 80)),
        )


@dataclass
class Configuration:
    """Main application configuration."""

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
        """Create Configuration from dictionary.

        Args:
            obj: Dictionary containing configuration data.

        Returns:
            Configuration instance.
        """
        # API Keys (prioritize config file, fallback to environment)
        deepgram_api_key = str(
            obj.get("deepgram_api_key") or os.getenv("DEEPGRAM_API_KEY", "")
        )
        openrouter_api_key = str(
            obj.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY", "")
        )

        # STT Configuration
        stt_model = str(obj.get("stt_model", "nova-2"))
        stt_language = str(obj.get("stt_language", "th"))
        stt_punctuate = bool(obj.get("stt_punctuate", True))

        # Audio Configuration
        audio_obj = obj.get("audio", {})
        audio = AudioConfig(
            sample_rate=int(audio_obj.get("sample_rate", 16000)),
            frame_ms=int(audio_obj.get("frame_ms", 20)),
            min_audio_bytes=int(audio_obj.get("min_audio_bytes", 6000)),
            output_sample_rate=int(audio_obj.get("output_sample_rate", 24000)),
            output_blocksize=int(audio_obj.get("output_blocksize", 1024)),
        )

        # VAD Configuration
        vad_obj = obj.get("vad", {})
        vad = VADConfig(
            padding_frames=int(vad_obj.get("padding_frames", 4)),
            max_silence_frames=int(vad_obj.get("max_silence_frames", 10)),
            rms_threshold=int(vad_obj.get("rms_threshold", 180)),
        )

        # TTS Configuration
        tts_obj = obj.get("tts", {})
        if "key" not in tts_obj:
            tts_obj["key"] = os.getenv("EDGE_TTS_KEY", "")
        tts = TTS.from_dict(tts_obj)

        # LLM Configuration
        llm = LLM.from_dict(obj.get("llm", {}))

        return Configuration(
            deepgram_api_key=deepgram_api_key,
            openrouter_api_key=openrouter_api_key,
            stt_model=stt_model,
            stt_language=stt_language,
            stt_punctuate=stt_punctuate,
            audio=audio,
            vad=vad,
            tts=tts,
            llm=llm,
        )

    @staticmethod
    @lru_cache
    def get_config() -> "Configuration":
        """Load configuration from file or environment.

        Returns:
            Configuration instance.
        """
        load_dotenv(".env")
        site = os.environ.get("SITE", DEFAULT_CONFIG_SITE)
        config_path = CONFIG_FILE_TEMPLATE.format(site=site)

        if os.path.exists(config_path):
            logger.info("Loading configuration from: %s", config_path)
            try:
                with open(config_path, encoding="utf-8") as file:
                    config_json = json.load(file)
                    return Configuration.from_dict(config_json)
            except (json.JSONDecodeError, IOError) as exc:
                logger.error("Failed to load config file: %s", exc)

        logger.warning("Config file not found, using defaults and environment variables")
        return Configuration.from_dict({})


def load_config() -> Configuration:
    """Load and validate configuration.

    Returns:
        Validated Configuration instance.

    Raises:
        RuntimeError: If required API keys are missing.
    """
    config = Configuration.get_config()

    # Validate required API keys
    if not config.deepgram_api_key:
        raise RuntimeError(
            "Missing DEEPGRAM_API_KEY. Set it in config file or environment."
        )

    if not config.openrouter_api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY. Set it in config file or environment."
        )

    if not config.tts.key:
        raise RuntimeError(
            "Missing EDGE_TTS_KEY. Set it in config file or environment."
        )

    logger.info("Configuration validated successfully")
    return config
