"""Sound cues adapter using synthesized tones played via sounddevice."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from hey_clever.ports.sound_cues import ISoundCues

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000


def _tone(freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    return (volume * 32767 * np.sin(2 * np.pi * freq * t)).astype(np.int16)


def _play(audio: np.ndarray) -> None:
    try:
        import sounddevice as sd

        sd.play(audio, samplerate=SAMPLE_RATE, blocksize=4096)
        sd.wait()
    except Exception as e:
        log.warning("Could not play sound cue: %s", e)


class BeepSoundCues(ISoundCues):
    def on_keyword_detected(self) -> None:
        _play(_tone(880, 0.15))

    def on_recording_done(self) -> None:
        _play(_tone(440, 0.2))

    def on_processing(self) -> None:
        blip = _tone(660, 0.08)
        gap = np.zeros(int(SAMPLE_RATE * 0.06), dtype=np.int16)
        _play(np.concatenate([blip, gap, blip]))

    def on_response_ready(self) -> None:
        # ascending three-note tone
        notes = [_tone(f, 0.1) for f in (440, 660, 880)]
        _play(np.concatenate(notes))
