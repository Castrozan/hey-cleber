"""Numpy-backed ring buffer for audio chunks."""

from __future__ import annotations

from collections import deque

import numpy as np


class AudioBuffer:
    """Fixed-capacity buffer that evicts oldest chunks when full."""

    def __init__(self, max_duration: float, sample_rate: int) -> None:
        self._max_samples = int(max_duration * sample_rate)
        self._sample_rate = sample_rate
        self._chunks: deque[np.ndarray] = deque()
        self._total_samples = 0

    @property
    def duration(self) -> float:
        return self._total_samples / self._sample_rate

    @property
    def is_empty(self) -> bool:
        return self._total_samples == 0

    def add(self, chunk: np.ndarray) -> None:
        self._chunks.append(chunk)
        self._total_samples += len(chunk)
        while self._total_samples > self._max_samples and self._chunks:
            evicted = self._chunks.popleft()
            self._total_samples -= len(evicted)

    def get_audio(self) -> np.ndarray:
        if not self._chunks:
            return np.array([], dtype=np.int16)
        return np.concatenate(list(self._chunks))

    def clear(self) -> None:
        self._chunks.clear()
        self._total_samples = 0
