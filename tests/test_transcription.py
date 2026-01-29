"""Tests for transcription processing (mock whisper)."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np

from hey_cleber.transcription import transcribe_tiny


class MockSegment:
    """Mock whisper segment."""

    def __init__(self, text: str) -> None:
        self.text = text


class TestTranscribeTiny:
    """Tests for the in-process whisper tiny transcription."""

    def test_basic_transcription(self) -> None:
        model = MagicMock()
        model.transcribe.return_value = (
            [MockSegment("hello"), MockSegment("world")],
            MagicMock(),
        )
        audio = np.zeros(16000, dtype=np.int16)
        result = transcribe_tiny(model, audio)
        assert result == "hello world"

    def test_empty_result(self) -> None:
        model = MagicMock()
        model.transcribe.return_value = ([], MagicMock())
        audio = np.zeros(16000, dtype=np.int16)
        result = transcribe_tiny(model, audio)
        assert result == ""

    def test_single_segment(self) -> None:
        model = MagicMock()
        model.transcribe.return_value = (
            [MockSegment("hey cleber")],
            MagicMock(),
        )
        audio = np.zeros(16000, dtype=np.int16)
        result = transcribe_tiny(model, audio)
        assert result == "hey cleber"

    def test_exception_handling(self) -> None:
        model = MagicMock()
        model.transcribe.side_effect = RuntimeError("model error")
        audio = np.zeros(16000, dtype=np.int16)
        result = transcribe_tiny(model, audio)
        assert result == ""

    def test_audio_normalization(self) -> None:
        """Verify that int16 audio is normalized to float32."""
        model = MagicMock()
        model.transcribe.return_value = ([MockSegment("test")], MagicMock())
        audio = np.array([32767, -32768, 0], dtype=np.int16)
        transcribe_tiny(model, audio)

        call_args = model.transcribe.call_args
        audio_arg = call_args[0][0]
        assert audio_arg.dtype == np.float32
        assert audio_arg.max() <= 1.0
        assert audio_arg.min() >= -1.1
