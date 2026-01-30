"""Tests for logging configuration."""

import logging

from hey_clever.config.logging_config import setup_logging


class TestSetupLogging:
    def test_debug_mode(self):
        setup_logging(debug=True)
        assert logging.getLogger().level == logging.DEBUG

    def test_info_mode(self):
        setup_logging(debug=False)
        assert logging.getLogger().level == logging.INFO

    def test_noisy_loggers_suppressed(self):
        setup_logging(debug=False)
        for name in ("httpcore", "httpx", "faster_whisper", "urllib3"):
            assert logging.getLogger(name).level == logging.WARNING
