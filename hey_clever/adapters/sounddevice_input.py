"""SoundDevice audio input adapter."""

from __future__ import annotations

import logging
import queue

import numpy as np
import sounddevice as sd

from hey_clever.config.settings import AudioConfig
from hey_clever.ports.audio_input import IAudioInput

log = logging.getLogger(__name__)


class SoundDeviceInput(IAudioInput):
    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._queue: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._muted = False

    def start_stream(self) -> None:
        device_kwargs: dict = {}
        if self._config.device is not None:
            device_kwargs["device"] = self._config.device

        self._stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._config.block_size,
            dtype="float32",
            callback=self._callback,
            **device_kwargs,
        )
        self._stream.start()
        log.info(
            "Audio stream started (rate=%d, block=%d)",
            self._config.sample_rate,
            self._config.block_size,
        )

    def stop_stream(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read_chunk(self) -> np.ndarray | None:
        try:
            return self._queue.get(timeout=1.0)
        except queue.Empty:
            return None

    def get_sample_rate(self) -> int:
        return self._config.sample_rate

    def is_muted(self) -> bool:
        return self._muted

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        if muted:
            # drain stale audio
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

    def _callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            log.debug("Audio status: %s", status)
        if self._muted:
            return
        block = (indata[:, 0] * 32767).astype(np.int16)
        self._queue.put(block)
