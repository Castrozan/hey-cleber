"""Tests for EdgeTTS adapter."""

from unittest.mock import MagicMock, patch

from hey_clever.adapters.edge_tts_adapter import EdgeTTSAdapter
from hey_clever.config.settings import TTSConfig


def _make_tts() -> EdgeTTSAdapter:
    return EdgeTTSAdapter(TTSConfig(mpv_bin="/usr/bin/mpv"))


class TestEdgeTTSAdapter:
    def test_not_speaking_initially(self):
        tts = _make_tts()
        assert tts.is_speaking() is False

    def test_stop(self):
        tts = _make_tts()
        tts.stop()
        assert tts.is_speaking() is False

    @patch("hey_clever.adapters.edge_tts_adapter.subprocess.run")
    @patch("hey_clever.adapters.edge_tts_adapter.os.path.exists", return_value=True)
    @patch("hey_clever.adapters.edge_tts_adapter.os.path.getsize", return_value=1000)
    @patch("hey_clever.adapters.edge_tts_adapter.os.unlink")
    def test_speak_success(self, mock_unlink, mock_size, mock_exists, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        tts = _make_tts()
        result = tts.speak("hello")
        assert result is False
        assert tts.is_speaking() is False

    @patch("hey_clever.adapters.edge_tts_adapter.subprocess.run")
    @patch("hey_clever.adapters.edge_tts_adapter.os.path.exists", return_value=True)
    @patch("hey_clever.adapters.edge_tts_adapter.os.unlink")
    def test_speak_edge_tts_failure_tries_fallback(self, mock_unlink, mock_exists, mock_run):
        mock_run.side_effect = Exception("edge-tts broken")
        tts = _make_tts()
        result = tts.speak("hello")
        assert result is False
