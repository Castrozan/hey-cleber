"""Tests for configuration parsing."""


import pytest

from hey_cleber.config import DEFAULT_KEYWORDS, AppConfig, parse_args


class TestAppConfig:
    """Tests for AppConfig dataclass."""

    def test_defaults(self):
        cfg = AppConfig()
        assert cfg.sample_rate == 16000
        assert cfg.channels == 1
        assert cfg.block_size == 512
        assert cfg.silence_threshold == 300.0
        assert cfg.vad_threshold == 0.4
        assert cfg.debug is False
        assert cfg.device is None
        assert len(cfg.keywords) == len(DEFAULT_KEYWORDS)

    def test_frozen(self):
        cfg = AppConfig()
        with pytest.raises(AttributeError):
            cfg.debug = True  # type: ignore[misc]

    def test_custom_values(self):
        cfg = AppConfig(
            silence_threshold=500.0,
            vad_threshold=0.6,
            keywords=("jarvis",),
            debug=True,
            device=3,
        )
        assert cfg.silence_threshold == 500.0
        assert cfg.vad_threshold == 0.6
        assert cfg.keywords == ("jarvis",)
        assert cfg.debug is True
        assert cfg.device == 3


class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_defaults(self):
        cfg = parse_args([])
        assert cfg.debug is False
        assert cfg.device is None
        assert cfg.keywords == tuple(DEFAULT_KEYWORDS)

    def test_debug_flag(self):
        cfg = parse_args(["--debug"])
        assert cfg.debug is True

    def test_device(self):
        cfg = parse_args(["--device", "2"])
        assert cfg.device == 2

    def test_custom_keywords(self):
        cfg = parse_args(["--keywords", "jarvis,friday"])
        assert cfg.keywords == ("jarvis", "friday")

    def test_silence_threshold(self):
        cfg = parse_args(["--silence-threshold", "500"])
        assert cfg.silence_threshold == 500.0

    def test_vad_threshold(self):
        cfg = parse_args(["--vad-threshold", "0.6"])
        assert cfg.vad_threshold == 0.6

    def test_env_gateway_url(self, monkeypatch):
        monkeypatch.setenv("CLAWDBOT_GATEWAY_URL", "http://example.com:9999")
        cfg = parse_args([])
        assert cfg.gateway_url == "http://example.com:9999"

    def test_env_whisper_bin(self, monkeypatch):
        monkeypatch.setenv("WHISPER_BIN", "/usr/bin/whisper")
        cfg = parse_args([])
        assert cfg.whisper_bin == "/usr/bin/whisper"

    def test_list_devices(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_args(["--list-devices"])
        assert exc_info.value.code == 0
