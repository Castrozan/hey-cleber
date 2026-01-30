"""Tests for DetectorState enum."""

from hey_clever.domain.detector_state import DetectorState


class TestDetectorState:
    def test_all_states_exist(self):
        assert DetectorState.IDLE.value == "idle"
        assert DetectorState.LISTENING.value == "listening"
        assert DetectorState.ACTIVATED.value == "activated"
        assert DetectorState.PROCESSING.value == "processing"
        assert DetectorState.RESPONDING.value == "responding"

    def test_state_count(self):
        assert len(DetectorState) == 5
