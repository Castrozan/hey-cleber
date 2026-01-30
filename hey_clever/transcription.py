"""Whisper transcription: in-process tiny model and CLI small model."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from typing import Any

import numpy as np

from .audio import save_wav
from .config import AppConfig

log = logging.getLogger("hey-clever.transcription")


def transcribe_tiny(whisper_model: Any, audio: np.ndarray) -> str:
    """Transcribe audio using the in-process faster-whisper tiny model.

    Args:
        whisper_model: A faster_whisper.WhisperModel instance.
        audio: int16 numpy array of audio samples.

    Returns:
        Transcribed text string.
    """
    audio_f32 = audio.astype(np.float32) / 32767.0
    try:
        segments, _info = whisper_model.transcribe(
            audio_f32,
            beam_size=1,
            best_of=1,
            language=None,  # auto-detect (could be EN or PT)
            vad_filter=False,  # we already did VAD
        )
        return " ".join(seg.text for seg in segments).strip()
    except Exception as e:
        log.error("Whisper tiny transcription failed: %s", e)
        return ""


def transcribe_full(audio: np.ndarray, config: AppConfig) -> str:
    """Transcribe audio using the Whisper CLI (small model) for high quality.

    Args:
        audio: int16 numpy array of audio samples.
        config: Application configuration.

    Returns:
        Transcribed text string.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
        save_wav(audio, wav_path, sample_rate=config.sample_rate)

    try:
        result = subprocess.run(
            [
                config.whisper_bin,
                wav_path,
                "--model",
                "small",
                "--language",
                "en",
                "--output_format",
                "txt",
                "--output_dir",
                tempfile.gettempdir(),
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        txt_path = wav_path.rsplit(".", 1)[0] + ".txt"
        if os.path.exists(txt_path):
            text = open(txt_path).read().strip()
            os.unlink(txt_path)
            return text
        else:
            log.warning("Whisper txt output not found, using stdout")
            return result.stdout.strip()
    except subprocess.TimeoutExpired:
        log.error("Whisper timed out")
        return ""
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)
