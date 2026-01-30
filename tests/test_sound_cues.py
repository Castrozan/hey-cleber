"""Tests for BeepSoundCues adapter."""

from unittest.mock import patch

import numpy as np

from hey_clever.adapters.beep_sound_cues import BeepSoundCues, _tone


class TestToneGeneration:
    def test_tone_dtype(self):
        t = _tone(880, 0.15)
        assert t.dtype == np.int16

    def test_tone_length(self):
        t = _tone(880, 0.15)
        expected = int(16000 * 0.15)
        assert len(t) == expected

    def test_tone_not_silent(self):
        t = _tone(440, 0.1)
        assert np.max(np.abs(t)) > 0

    def test_zero_volume(self):
        t = _tone(440, 0.1, volume=0.0)
        assert np.max(np.abs(t)) == 0


class TestBeepSoundCues:
    @patch("hey_clever.adapters.beep_sound_cues._play")
    def test_on_keyword_detected(self, mock_play):
        cues = BeepSoundCues()
        cues.on_keyword_detected()
        mock_play.assert_called_once()
        audio = mock_play.call_args[0][0]
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.int16

    @patch("hey_clever.adapters.beep_sound_cues._play")
    def test_on_recording_done(self, mock_play):
        cues = BeepSoundCues()
        cues.on_recording_done()
        mock_play.assert_called_once()

    @patch("hey_clever.adapters.beep_sound_cues._play")
    def test_on_processing(self, mock_play):
        cues = BeepSoundCues()
        cues.on_processing()
        mock_play.assert_called_once()
        audio = mock_play.call_args[0][0]
        # double blip: should be longer than a single tone
        assert len(audio) > int(16000 * 0.08)

    @patch("hey_clever.adapters.beep_sound_cues._play")
    def test_on_response_ready(self, mock_play):
        cues = BeepSoundCues()
        cues.on_response_ready()
        mock_play.assert_called_once()
        audio = mock_play.call_args[0][0]
        # ascending 3-note tone
        assert len(audio) == int(16000 * 0.1) * 3
