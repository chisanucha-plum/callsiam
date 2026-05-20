import queue
import subprocess
import threading

import numpy as np
import sounddevice as sd

from app.configuration import Configuration


class AudioOutput:
    def __init__(self, config: Configuration):
        self._queue = queue.Queue()
        self._output_rate = config.audio.output_sample_rate
        self._stream = sd.OutputStream(
            samplerate=self._output_rate,
            channels=1,
            dtype="int16",
            blocksize=config.audio.output_blocksize,
        )
        self._stream.start()
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )
        self._thread.start()

    def enqueue(self, mp3_bytes: bytes) -> None:
        if mp3_bytes:
            self._queue.put(mp3_bytes)

    def close(self) -> None:
        self._queue.put(None)
        self._stream.stop()
        self._stream.close()

    def _loop(self) -> None:
        while True:
            mp3 = self._queue.get()
            if mp3 is None:
                break
            self._play_mp3_fast(mp3)

    def _play_mp3_fast(self, mp3_bytes: bytes) -> None:
        try:
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    "pipe:0",
                    "-f",
                    "s16le",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    str(self._output_rate),
                    "-ac",
                    "1",
                    "pipe:1",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )

            pcm_audio, _ = process.communicate(
                input=mp3_bytes
            )

            audio = np.frombuffer(
                pcm_audio,
                dtype=np.int16,
            )

            if len(audio) > 0:
                self._stream.write(audio)

        except Exception as exc:
            print(f"\nAudio play error: {exc}")
