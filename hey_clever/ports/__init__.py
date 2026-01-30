"""Port interfaces (ABCs) for the hexagonal architecture."""

from hey_clever.ports.audio_input import IAudioInput
from hey_clever.ports.gateway import IGateway
from hey_clever.ports.keyword_detection import IKeywordDetector
from hey_clever.ports.sound_cues import ISoundCues
from hey_clever.ports.transcription import ITranscription
from hey_clever.ports.tts import ITTS

__all__ = [
    "IAudioInput",
    "IGateway",
    "IKeywordDetector",
    "ISoundCues",
    "ITranscription",
    "ITTS",
]
