"""Audio input/output services for microphone recording and speaker playback."""

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

# Constants
SLEEP_INTERVAL_MS = 1000


class AudioInput:
    """Captures audio from microphone and queues it for processing."""

    def __init__(self, config: Configuration, audio_queue: queue.Queue) -> None:
        """Initialize audio input.

        Args:
            config: Application configuration.
            audio_queue: Queue to put captured audio frames.
        """
        self._config = config
        self._audio_queue = audio_queue
        self._thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        logger.info("AudioInput initialized (sample_rate=%d)", config.audio.sample_rate)

    def start(self) -> None:
        """Start recording in background thread."""
        if self._is_running:
            logger.warning("AudioInput already running")
            return

        self._is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("AudioInput started")

    def stop(self) -> None:
        """Stop recording."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("AudioInput stopped")

    def _loop(self) -> None:
        """Recording loop."""
        def callback(indata, frames, time_info, status):
            if status:
                logger.warning("Audio status: %s", status)
            if self._is_running:
                self._audio_queue.put(bytes(indata))

        try:
            with sd.RawInputStream(
                samplerate=self._config.audio.sample_rate,
                channels=AUDIO_CHANNELS,
                dtype=AUDIO_DTYPE,
                blocksize=self._config.audio.frame_samples(),
                callback=callback,
            ):
                while self._is_running:
                    sd.sleep(SLEEP_INTERVAL_MS)
        except Exception as exc:
            logger.error("AudioInput error: %s", exc)
            self._is_running = False


class AudioOutput:
    """Converts MP3 to PCM and plays through speakers."""

    def __init__(self, config: Configuration) -> None:
        """Initialize audio output.

        Args:
            config: Application configuration.
        """
        self._queue: queue.Queue = queue.Queue()
        self._output_rate = config.audio.output_sample_rate
        self._ffmpeg_timeout = config.external_apis.ffmpeg_timeout
        self._is_running = True

        self._stream = sd.OutputStream(
            samplerate=self._output_rate,
            channels=AUDIO_CHANNELS,
            dtype=AUDIO_DTYPE,
            blocksize=config.audio.output_blocksize,
        )
        self._stream.start()

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("AudioOutput initialized (sample_rate=%d)", self._output_rate)

    def enqueue(self, mp3_bytes: bytes) -> None:
        """Queue MP3 audio for playback."""
        if mp3_bytes and self._is_running:
            self._queue.put(mp3_bytes)

    def close(self) -> None:
        """Stop and cleanup."""
        logger.info("Closing AudioOutput")
        self._is_running = False
        self._queue.put(None)

        if self._thread.is_alive():
            self._thread.join(timeout=2)

        try:
            self._stream.stop()
            self._stream.close()
        except Exception as exc:
            logger.error("Error closing stream: %s", exc)

    def _loop(self) -> None:
        """Playback loop."""
        while self._is_running:
            try:
                mp3_data = self._queue.get(timeout=1)
                if mp3_data is None:
                    break
                self._play_mp3(mp3_data)
            except queue.Empty:
                continue
            except Exception as exc:
                logger.error("Playback error: %s", exc)

    def _play_mp3(self, mp3_bytes: bytes) -> None:
        """Convert MP3 to PCM and play."""
        try:
            pcm_audio = self._convert_mp3_to_pcm(mp3_bytes)
            if pcm_audio:
                audio_array = np.frombuffer(pcm_audio, dtype=np.int16)
                if len(audio_array) > 0:
                    self._stream.write(audio_array)
        except Exception as exc:
            logger.error("Error playing MP3: %s", exc)

    def _convert_mp3_to_pcm(self, mp3_bytes: bytes) -> Optional[bytes]:
        """Convert MP3 to PCM using FFmpeg."""
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
                timeout=self._ffmpeg_timeout
            )

            if process.returncode != 0:
                logger.error("FFmpeg failed: %s", stderr.decode())
                return None

            return pcm_audio

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout (%ds)", self._ffmpeg_timeout)
            process.kill()
            return None
        except Exception as exc:
            logger.error("MP3 conversion error: %s", exc)
            return None
