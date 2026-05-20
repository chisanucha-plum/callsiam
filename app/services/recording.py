"""Audio recording service for capturing microphone input."""

import logging
import queue
import threading

import sounddevice as sd

from app.configuration import Configuration
from app.constants import AUDIO_CHANNELS, AUDIO_DTYPE

logger = logging.getLogger(__name__)

# Module-specific constants
SLEEP_INTERVAL_MS = 1000


class Recorder:
    """Captures audio from microphone and queues it for processing."""

    def __init__(self, config: Configuration, audio_input_q: queue.Queue) -> None:
        """Initialize audio recorder.

        Args:
            config: Application configuration containing audio settings.
            audio_input_q: Queue to put captured audio frames.
        """
        self._config = config
        self._audio_input_q = audio_input_q
        self._thread: threading.Thread = None
        self._is_running: bool = False
        logger.info("Recorder initialized with sample rate: %d", config.audio.sample_rate)

    def start(self) -> None:
        """Start recording audio in a background thread."""
        if self._is_running:
            logger.warning("Recorder is already running")
            return

        self._is_running = True
        self._thread = threading.Thread(
            target=self._recording_loop,
            daemon=True,
        )
        self._thread.start()
        logger.info("Recording started")

    def stop(self) -> None:
        """Stop recording audio."""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        logger.info("Recording stopped")

    def _recording_loop(self) -> None:
        """Main recording loop that captures audio from microphone."""
        def audio_callback(indata, frames, time_info, status):
            """Callback function for audio stream.

            Args:
                indata: Input audio data.
                frames: Number of frames.
                time_info: Time information.
                status: Stream status.
            """
            if status:
                logger.warning("Audio stream status: %s", status)

            if self._is_running:
                self._audio_input_q.put(bytes(indata))

        try:
            with sd.RawInputStream(
                samplerate=self._config.audio.sample_rate,
                channels=AUDIO_CHANNELS,
                dtype=AUDIO_DTYPE,
                blocksize=self._config.audio.frame_samples(),
                callback=audio_callback,
            ):
                while self._is_running:
                    sd.sleep(SLEEP_INTERVAL_MS)
        except Exception as exc:
            logger.error("Error in recording loop: %s", exc)
            self._is_running = False
