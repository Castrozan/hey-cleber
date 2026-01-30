from __future__ import annotations

from abc import ABC, abstractmethod


class IKeywordDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> tuple[bool, float]:
        """Returns (detected, confidence)."""

    @abstractmethod
    def get_keywords(self) -> tuple[str, ...]: ...
