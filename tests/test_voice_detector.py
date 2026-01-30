"""Tests for VoiceDetector orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from hey_clever.config.settings import Settings
from hey_clever.domain.detector_state import DetectorState
from hey_clever.domain.vad import SileroVAD
from hey_clever.domain.voice_detector import VoiceDetector, _rms


def _make_detector(
    vad_speech: list[bool] | None = None,
    kw_text: str = "",
    kw_detected: bool = False,
    cmd_text: str = "",
    gateway_response: str = "ok",
) -> tuple[VoiceDetector, dict[str, MagicMock]]:
    audio_input = MagicMock()
    audio_input.read_chunk.return_value = np.zeros(512, dtype=np.int16)
    audio_input.get_sample_rate.return_value = 16000

    vad = MagicMock(spec=SileroVAD)
    if vad_speech is not None:
        vad.is_speech.side_effect = vad_speech
    else:
        vad.is_speech.return_value = False

    kw_transcription = MagicMock()
    kw_transcription.transcribe.return_value = kw_text

    cmd_transcription = MagicMock()
    cmd_transcription.transcribe.return_value = cmd_text

    keyword_detector = MagicMock()
    keyword_detector.detect.return_value = (kw_detected, 1.0 if kw_detected else 0.0)

    gateway = MagicMock()
    gateway.send.return_value = gateway_response

    tts = MagicMock()
    sound_cues = MagicMock()

    settings = Settings.default()

    detector = VoiceDetector(
        audio_input=audio_input,
        vad=vad,
        keyword_transcription=kw_transcription,
        command_transcription=cmd_transcription,
        keyword_detector=keyword_detector,
        gateway=gateway,
        tts=tts,
        sound_cues=sound_cues,
        settings=settings,
    )

    mocks = {
        "audio_input": audio_input,
        "vad": vad,
        "kw_transcription": kw_transcription,
        "cmd_transcription": cmd_transcription,
        "keyword_detector": keyword_detector,
        "gateway": gateway,
        "tts": tts,
        "sound_cues": sound_cues,
    }
    return detector, mocks


class TestRms:
    def test_silence(self):
        assert _rms(np.zeros(512, dtype=np.int16)) == 0.0

    def test_nonzero(self):
        block = np.ones(512, dtype=np.int16) * 1000
        assert _rms(block) == pytest.approx(1000.0, rel=1e-3)


class TestVoiceDetectorInit:
    def test_initial_state(self):
        detector, _ = _make_detector()
        assert detector.state == DetectorState.IDLE
        assert detector.running is False

    def test_stop_when_not_running(self):
        detector, _ = _make_detector()
        detector.stop()
        assert detector.running is False


class TestHandleIdle:
    def test_no_speech_stays_idle(self):
        detector, mocks = _make_detector()
        chunk = np.zeros(512, dtype=np.int16)
        mocks["vad"].is_speech.return_value = False
        detector._handle_idle(chunk)
        assert detector.state == DetectorState.IDLE

    def test_speech_transitions_to_listening(self):
        detector, mocks = _make_detector()
        chunk = np.zeros(512, dtype=np.int16)
        mocks["vad"].is_speech.return_value = True
        detector._handle_idle(chunk)
        assert detector.state == DetectorState.LISTENING


class TestCheckKeyword:
    def test_keyword_detected_enters_activated(self):
        detector, mocks = _make_detector(kw_text="hey clever", kw_detected=True)
        detector._kw_buffer.add(np.zeros(512, dtype=np.int16))
        detector._check_keyword()
        assert detector.state == DetectorState.ACTIVATED
        mocks["sound_cues"].on_keyword_detected.assert_called_once()

    def test_no_keyword_resets_to_idle(self):
        detector, mocks = _make_detector(kw_text="hello world", kw_detected=False)
        detector._kw_buffer.add(np.zeros(512, dtype=np.int16))
        detector.state = DetectorState.LISTENING
        detector._check_keyword()
        assert detector.state == DetectorState.IDLE


class TestProcessCommand:
    def test_full_pipeline(self):
        detector, mocks = _make_detector(
            cmd_text="what time is it",
            gateway_response="It's 3 PM.",
        )
        detector.state = DetectorState.ACTIVATED
        detector._cmd_got_speech = True
        detector._cmd_buffer.add(np.ones(16000, dtype=np.int16) * 1000)

        detector._process_command()

        mocks["sound_cues"].on_recording_done.assert_called_once()
        mocks["cmd_transcription"].transcribe.assert_called_once()
        mocks["sound_cues"].on_processing.assert_called_once()
        mocks["gateway"].send.assert_called_once_with("what time is it")
        mocks["sound_cues"].on_response_ready.assert_called_once()
        mocks["tts"].speak.assert_called_once_with("It's 3 PM.")
        mocks["audio_input"].set_muted.assert_called()
        assert detector.state == DetectorState.IDLE

    def test_empty_transcription_resets(self):
        detector, mocks = _make_detector(cmd_text="")
        detector.state = DetectorState.ACTIVATED
        detector._cmd_got_speech = True
        detector._cmd_buffer.add(np.ones(16000, dtype=np.int16) * 1000)

        detector._process_command()

        mocks["gateway"].send.assert_not_called()
        assert detector.state == DetectorState.IDLE

    def test_too_short_recording_resets(self):
        detector, mocks = _make_detector(cmd_text="hello")
        detector.state = DetectorState.ACTIVATED
        detector._cmd_got_speech = True
        # add very short audio (less than min_duration)
        detector._cmd_buffer.add(np.ones(100, dtype=np.int16) * 1000)

        detector._process_command()

        mocks["cmd_transcription"].transcribe.assert_not_called()
        assert detector.state == DetectorState.IDLE

    def test_no_speech_resets(self):
        detector, mocks = _make_detector()
        detector.state = DetectorState.ACTIVATED
        detector._cmd_got_speech = False
        detector._cmd_buffer.add(np.ones(16000, dtype=np.int16))

        detector._process_command()

        mocks["cmd_transcription"].transcribe.assert_not_called()
        assert detector.state == DetectorState.IDLE


class TestStartStop:
    def test_start_and_stop(self):
        detector, mocks = _make_detector()
        mocks["audio_input"].read_chunk.side_effect = KeyboardInterrupt
        detector.start()
        assert detector.running is False
        mocks["audio_input"].start_stream.assert_called_once()
        mocks["audio_input"].stop_stream.assert_called_once()
