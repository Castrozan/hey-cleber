"""Voice detector state machine states."""

from __future__ import annotations

from enum import Enum


class DetectorState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ACTIVATED = "activated"
    PROCESSING = "processing"
    RESPONDING = "responding"
