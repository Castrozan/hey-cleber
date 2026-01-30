"""Tests for AudioBuffer domain object."""

import numpy as np
import pytest

from hey_clever.domain.audio_buffer import AudioBuffer


class TestAudioBuffer:
    def test_empty_buffer(self):
        buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
        assert buf.is_empty
        assert buf.duration == 0.0
        assert len(buf.get_audio()) == 0

    def test_add_and_get(self):
        buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
        chunk = np.ones(512, dtype=np.int16)
        buf.add(chunk)
        assert not buf.is_empty
        assert buf.duration == pytest.approx(512 / 16000, rel=1e-3)
        audio = buf.get_audio()
        assert len(audio) == 512
        np.testing.assert_array_equal(audio, chunk)

    def test_multiple_chunks(self):
        buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
        for _ in range(10):
            buf.add(np.zeros(512, dtype=np.int16))
        assert len(buf.get_audio()) == 5120
        assert buf.duration == pytest.approx(5120 / 16000, rel=1e-3)

    def test_eviction_on_overflow(self):
        buf = AudioBuffer(max_duration=0.1, sample_rate=16000)
        # 0.1s at 16kHz = 1600 samples max
        for _ in range(10):
            buf.add(np.ones(512, dtype=np.int16))
        audio = buf.get_audio()
        assert len(audio) <= 1600 + 512  # at most one chunk over

    def test_clear(self):
        buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
        buf.add(np.ones(512, dtype=np.int16))
        buf.clear()
        assert buf.is_empty
        assert buf.duration == 0.0

    def test_get_audio_preserves_data(self):
        buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
        chunk = np.array([100, 200, 300, -100], dtype=np.int16)
        buf.add(chunk)
        np.testing.assert_array_equal(buf.get_audio(), chunk)
