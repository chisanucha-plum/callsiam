"""Audio output service for playing MP3 audio through speakers."""

import logging
import queue
import subprocess
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from app.configuration import Configuration
from app.constants import AUDIO_CHANNELS, AUDIO_DTYPE

logger = logging.getLogger(__name__)

# Module-specific constants
FFMPEG_TIMEOUT_SECONDS = 10


class AudioOutput:
    """Handles audio playback by converting MP3 to PCM and streaming to speakers."""

    def __init__(self, config: Configuration) -> None:
        """Initialize audio output with configuration.

        Args:
            config: Application configuration containing audio settings.
        """
        self._queue: queue.Queue = queue.Queue()
        self._output_rate: int = config.audio.output_sample_rate
        self._is_running: bool = True
        
        self._stream: sd.OutputStream = sd.OutputStream(
            samplerate=self._output_rate,
            channels=AUDIO_CHANNELS,
            dtype=AUDIO_DTYPE,
            blocksize=config.audio.output_blocksize,
        )
        self._stream.start()
        
        self._thread: threading.Thread = threading.Thread(
            target=self._playback_loop,
            daemon=True,
        )
        self._thread.start()
        logger.info("Audio output initialized with sample rate: %d", self._output_rate)

    def enqueue(self, mp3_bytes: bytes) -> None:
        """Add MP3 audio data to the playback queue.

        Args:
            mp3_bytes: MP3 audio data as bytes.
        """
        if mp3_bytes and self._is_running:
            self._queue.put(mp3_bytes)

    def close(self) -> None:
        """Stop playback and clean up resources."""
        logger.info("Closing audio output")
        self._is_running = False
        self._queue.put(None)
        
        if self._thread.is_alive():
            self._thread.join(timeout=2)
        
        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            logger.error("Error closing audio stream: %s", exc)

    def _playback_loop(self) -> None:
        """Main playback loop that processes queued audio."""
        while self._is_running:
            try:
                mp3_data = self._queue.get(timeout=1)
                if mp3_data is None:
                    break
                self._play_mp3(mp3_data)
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error("Error in playback loop: %s", exc)

    def _play_mp3(self, mp3_bytes: bytes) -> None:
        """Convert MP3 to PCM and play through audio stream.

        Args:
            mp3_bytes: MP3 audio data to play.
        """
        try:
            pcm_audio = self._convert_mp3_to_pcm(mp3_bytes)
            if pcm_audio:
                self._write_to_stream(pcm_audio)
        except Exception as exc:
            logger.error("Error playing MP3 audio: %s", exc)

    def _convert_mp3_to_pcm(self, mp3_bytes: bytes) -> Optional[bytes]:
        """Convert MP3 bytes to PCM format using FFmpeg.

        Args:
            mp3_bytes: MP3 audio data.

        Returns:
            PCM audio data or None if conversion fails.
        """
        try:
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", "pipe:0",
                    "-f", "s16le",
                    "-acodec", "pcm_s16le",
                    "-ar", str(self._output_rate),
                    "-ac", str(AUDIO_CHANNELS),
                    "pipe:1",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            pcm_audio, stderr = process.communicate(
                input=mp3_bytes,
                timeout=FFMPEG_TIMEOUT_SECONDS
            )

            if process.returncode != 0:
                logger.error("FFmpeg conversion failed: %s", stderr.decode())
                return None

            return pcm_audio

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg conversion timed out")
            process.kill()
            return None
        except Exception as exc:
            logger.error("Error converting MP3 to PCM: %s", exc)
            return None

    def _write_to_stream(self, pcm_audio: bytes) -> None:
        """Write PCM audio data to the output stream.

        Args:
            pcm_audio: PCM audio data to write.
        """
        try:
            audio_array = np.frombuffer(pcm_audio, dtype=np.int16)
            if len(audio_array) > 0:
                self._stream.write(audio_array)
        except Exception as exc:
            logger.error("Error writing to audio stream: %s", exc)
