from __future__ import annotations

from abc import ABC, abstractmethod


class ISoundCues(ABC):
    @abstractmethod
    def on_keyword_detected(self) -> None: ...

    @abstractmethod
    def on_recording_done(self) -> None: ...

    @abstractmethod
    def on_processing(self) -> None: ...

    @abstractmethod
    def on_response_ready(self) -> None: ...
