"""Tests for Whisper transcription adapters."""

import subprocess
from unittest.mock import MagicMock, patch

import numpy as np

from hey_clever.adapters.whisper_transcription import (
    WhisperCLITranscription,
    WhisperTinyTranscription,
)
from hey_clever.config.settings import TranscriptionConfig


class TestWhisperTinyTranscription:
    def test_transcribe_success(self):
        mock_model = MagicMock()
        seg = MagicMock()
        seg.text = "hello world"
        mock_model.transcribe.return_value = ([seg], None)

        adapter = WhisperTinyTranscription(model=mock_model)
        audio = np.zeros(16000, dtype=np.int16)
        result = adapter.transcribe(audio)
        assert result == "hello world"

    def test_transcribe_multiple_segments(self):
        mock_model = MagicMock()
        seg1 = MagicMock(text="hello")
        seg2 = MagicMock(text="world")
        mock_model.transcribe.return_value = ([seg1, seg2], None)

        adapter = WhisperTinyTranscription(model=mock_model)
        result = adapter.transcribe(np.zeros(16000, dtype=np.int16))
        assert result == "hello world"

    def test_transcribe_empty(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], None)

        adapter = WhisperTinyTranscription(model=mock_model)
        result = adapter.transcribe(np.zeros(16000, dtype=np.int16))
        assert result == ""

    def test_transcribe_error(self):
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("model error")

        adapter = WhisperTinyTranscription(model=mock_model)
        result = adapter.transcribe(np.zeros(16000, dtype=np.int16))
        assert result == ""

    def test_converts_int16_to_float32(self):
        mock_model = MagicMock()
        mock_model.transcribe.return_value = ([], None)

        adapter = WhisperTinyTranscription(model=mock_model)
        audio = np.array([32767, -32767], dtype=np.int16)
        adapter.transcribe(audio)

        call_args = mock_model.transcribe.call_args[0][0]
        assert call_args.dtype == np.float32
        assert abs(call_args[0] - 1.0) < 0.001


class TestWhisperCLITranscription:
    @patch("hey_clever.adapters.whisper_transcription.os.unlink")
    @patch("hey_clever.adapters.whisper_transcription.os.path.exists", return_value=False)
    @patch("hey_clever.adapters.whisper_transcription.subprocess.run")
    def test_transcribe_stdout_fallback(self, mock_run, mock_exists, mock_unlink):
        mock_run.return_value = MagicMock(returncode=0, stdout="transcribed text")

        config = TranscriptionConfig(whisper_bin="/usr/bin/whisper")
        adapter = WhisperCLITranscription(config)
        result = adapter.transcribe(np.zeros(16000, dtype=np.int16))
        assert result == "transcribed text"

    @patch("hey_clever.adapters.whisper_transcription.os.unlink")
    @patch("hey_clever.adapters.whisper_transcription.os.path.exists", return_value=True)
    @patch("hey_clever.adapters.whisper_transcription.subprocess.run")
    def test_transcribe_timeout(self, mock_run, mock_exists, mock_unlink):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="whisper", timeout=120)

        config = TranscriptionConfig(whisper_bin="/usr/bin/whisper")
        adapter = WhisperCLITranscription(config)
        result = adapter.transcribe(np.zeros(16000, dtype=np.int16))
        assert result == ""

    @patch("hey_clever.adapters.whisper_transcription.os.unlink")
    @patch("hey_clever.adapters.whisper_transcription.os.path.exists", return_value=False)
    @patch("hey_clever.adapters.whisper_transcription.subprocess.run")
    def test_calls_whisper_cli(self, mock_run, mock_exists, mock_unlink):
        mock_run.return_value = MagicMock(returncode=0, stdout="text")

        config = TranscriptionConfig(
            whisper_bin="/custom/whisper", command_model="medium", language="pt"
        )
        adapter = WhisperCLITranscription(config)
        adapter.transcribe(np.zeros(16000, dtype=np.int16))

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/custom/whisper"
        assert "--model" in call_args
        idx = call_args.index("--model")
        assert call_args[idx + 1] == "medium"

    def test_save_wav_creates_file(self, tmp_path):
        audio = np.array([100, -100, 200, -200], dtype=np.int16)

        import os
        import wave

        # Use the static method directly
        fd, path = __import__("tempfile").mkstemp(suffix=".wav", dir=str(tmp_path))
        os.close(fd)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio.tobytes())

        assert os.path.exists(path)
        with wave.open(path, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == 16000
