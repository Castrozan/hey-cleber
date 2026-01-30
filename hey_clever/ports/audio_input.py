from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class IAudioInput(ABC):
    @abstractmethod
    def start_stream(self) -> None: ...

    @abstractmethod
    def stop_stream(self) -> None: ...

    @abstractmethod
    def read_chunk(self) -> np.ndarray | None:
        """Returns None on timeout."""

    @abstractmethod
    def get_sample_rate(self) -> int: ...

    @abstractmethod
    def is_muted(self) -> bool: ...

    @abstractmethod
    def set_muted(self, muted: bool) -> None: ...
