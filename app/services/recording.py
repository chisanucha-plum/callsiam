import threading

import sounddevice as sd

from app.configuration import Configuration


class Recorder:
    def __init__(self, config: Configuration, audio_input_q):
        self._config = config
        self._audio_input_q = audio_input_q
        self._thread = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )
        self._thread.start()

    def _loop(self) -> None:
        def callback(indata, frames, time_info, status):
            if status:
                return

            self._audio_input_q.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=self._config.audio.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self._config.audio.frame_samples(),
            callback=callback,
        ):
            while True:
                sd.sleep(1000)
