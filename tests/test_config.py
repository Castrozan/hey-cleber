"""Tests for configuration and settings."""

import pytest

from hey_clever.config.settings import (
    AudioConfig,
    GatewayConfig,
    KeywordConfig,
    RecordingConfig,
    Settings,
    TranscriptionConfig,
    TTSConfig,
    VADConfig,
)


class TestAudioConfig:
    def test_defaults(self):
        cfg = AudioConfig()
        assert cfg.sample_rate == 16000
        assert cfg.channels == 1
        assert cfg.block_size == 512
        assert cfg.device is None

    def test_frozen(self):
        cfg = AudioConfig()
        with pytest.raises(AttributeError):
            cfg.sample_rate = 44100  # type: ignore[misc]


class TestVADConfig:
    def test_defaults(self):
        cfg = VADConfig()
        assert cfg.threshold == 0.4
        assert cfg.silence_duration == 0.8
        assert cfg.min_speech_duration == 0.3
        assert cfg.max_buffer_sec == 5.0


class TestRecordingConfig:
    def test_defaults(self):
        cfg = RecordingConfig()
        assert cfg.silence_threshold == 300.0
        assert cfg.silence_duration == 2.0
        assert cfg.max_duration == 30.0
        assert cfg.min_duration == 0.5


class TestKeywordConfig:
    def test_defaults(self):
        cfg = KeywordConfig()
        assert "clever" in cfg.keywords
        assert "cleber" in cfg.keywords

    def test_custom_keywords(self):
        cfg = KeywordConfig(keywords=("jarvis",))
        assert cfg.keywords == ("jarvis",)


class TestTranscriptionConfig:
    def test_defaults(self):
        cfg = TranscriptionConfig()
        assert cfg.keyword_model == "tiny"
        assert cfg.command_model == "small"
        assert cfg.language == "en"


class TestGatewayConfig:
    def test_defaults(self):
        cfg = GatewayConfig()
        assert cfg.url == "http://localhost:18789"
        assert cfg.token == ""
        assert cfg.timeout == 60


class TestTTSConfig:
    def test_defaults(self):
        cfg = TTSConfig()
        assert cfg.voice == "en-US-GuyNeural"


class TestSettings:
    def test_defaults(self):
        s = Settings.default()
        assert s.debug is False
        assert isinstance(s.audio, AudioConfig)
        assert isinstance(s.vad, VADConfig)
        assert isinstance(s.recording, RecordingConfig)
        assert isinstance(s.keyword, KeywordConfig)
        assert isinstance(s.transcription, TranscriptionConfig)
        assert isinstance(s.gateway, GatewayConfig)
        assert isinstance(s.tts, TTSConfig)

    def test_frozen(self):
        s = Settings.default()
        with pytest.raises(AttributeError):
            s.debug = True  # type: ignore[misc]

    def test_from_args_defaults(self):
        s = Settings.from_args([])
        assert s.debug is False
        assert s.audio.device is None

    def test_from_args_debug(self):
        s = Settings.from_args(["--debug"])
        assert s.debug is True

    def test_from_args_device(self):
        s = Settings.from_args(["--device", "3"])
        assert s.audio.device == 3

    def test_from_args_keywords(self):
        s = Settings.from_args(["--keywords", "jarvis,friday"])
        assert s.keyword.keywords == ("jarvis", "friday")

    def test_from_args_vad_threshold(self):
        s = Settings.from_args(["--vad-threshold", "0.6"])
        assert s.vad.threshold == 0.6

    def test_from_args_silence_threshold(self):
        s = Settings.from_args(["--silence-threshold", "500"])
        assert s.recording.silence_threshold == 500.0

    def test_from_args_env_gateway(self, monkeypatch):
        monkeypatch.setenv("CLAWDBOT_GATEWAY_URL", "http://example.com:9999")
        s = Settings.from_args([])
        assert s.gateway.url == "http://example.com:9999"

    def test_from_args_env_whisper(self, monkeypatch):
        monkeypatch.setenv("WHISPER_BIN", "/usr/bin/whisper")
        s = Settings.from_args([])
        assert s.transcription.whisper_bin == "/usr/bin/whisper"

    def test_list_devices(self, monkeypatch):
        import sys
        import types

        mock_sd = types.ModuleType("sounddevice")
        mock_sd.query_devices = lambda: "Mock Device List"  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "sounddevice", mock_sd)

        with pytest.raises(SystemExit) as exc_info:
            Settings.from_args(["--list-devices"])
        assert exc_info.value.code == 0
