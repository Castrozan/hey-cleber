"""Tests for audio helper functions."""

import numpy as np
import pytest

from hey_cleber.audio import generate_beep, rms


class TestRms:
    """Tests for RMS calculation."""

    def test_silence(self):
        block = np.zeros(512, dtype=np.int16)
        assert rms(block) == 0.0

    def test_nonzero(self):
        block = np.ones(512, dtype=np.int16) * 1000
        result = rms(block)
        assert result == pytest.approx(1000.0, rel=1e-3)

    def test_mixed_signal(self):
        block = np.array([100, -100, 100, -100], dtype=np.int16)
        assert rms(block) == pytest.approx(100.0, rel=1e-3)

    def test_single_sample(self):
        block = np.array([500], dtype=np.int16)
        assert rms(block) == pytest.approx(500.0, rel=1e-3)


class TestGenerateBeep:
    """Tests for beep generation."""

    def test_dtype(self):
        beep = generate_beep()
        assert beep.dtype == np.int16

    def test_length(self):
        beep = generate_beep(duration=0.15, sample_rate=16000)
        expected = int(16000 * 0.15)
        assert len(beep) == expected

    def test_not_silent(self):
        beep = generate_beep()
        assert np.max(np.abs(beep)) > 0

    def test_custom_frequency(self):
        beep = generate_beep(freq=440, duration=0.1, sample_rate=16000)
        assert len(beep) == int(16000 * 0.1)

    def test_volume_scaling(self):
        loud = generate_beep(volume=1.0)
        quiet = generate_beep(volume=0.1)
        assert np.max(np.abs(loud)) > np.max(np.abs(quiet))

    def test_zero_volume(self):
        beep = generate_beep(volume=0.0)
        assert np.max(np.abs(beep)) == 0
