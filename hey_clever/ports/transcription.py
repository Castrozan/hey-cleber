from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class ITranscription(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray) -> str: ...
