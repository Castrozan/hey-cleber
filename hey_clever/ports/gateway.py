from __future__ import annotations

from abc import ABC, abstractmethod


class IGateway(ABC):
    @abstractmethod
    def send(self, message: str, context: list[dict[str, str]] | None = None) -> str: ...
