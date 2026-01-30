"""Tests verifying port interfaces are proper ABCs that cannot be instantiated."""

import pytest

from hey_clever.ports.audio_input import IAudioInput
from hey_clever.ports.gateway import IGateway
from hey_clever.ports.keyword_detection import IKeywordDetector
from hey_clever.ports.sound_cues import ISoundCues
from hey_clever.ports.transcription import ITranscription
from hey_clever.ports.tts import ITTS


class TestPortsAreAbstract:
    def test_audio_input(self):
        with pytest.raises(TypeError):
            IAudioInput()  # type: ignore[abstract]

    def test_transcription(self):
        with pytest.raises(TypeError):
            ITranscription()  # type: ignore[abstract]

    def test_gateway(self):
        with pytest.raises(TypeError):
            IGateway()  # type: ignore[abstract]

    def test_tts(self):
        with pytest.raises(TypeError):
            ITTS()  # type: ignore[abstract]

    def test_keyword_detection(self):
        with pytest.raises(TypeError):
            IKeywordDetector()  # type: ignore[abstract]

    def test_sound_cues(self):
        with pytest.raises(TypeError):
            ISoundCues()  # type: ignore[abstract]
