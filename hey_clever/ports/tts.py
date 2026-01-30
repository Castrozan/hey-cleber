from __future__ import annotations

from abc import ABC, abstractmethod


class ITTS(ABC):
    @abstractmethod
    def speak(self, text: str) -> bool:
        """Returns True if interrupted."""

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def is_speaking(self) -> bool: ...
