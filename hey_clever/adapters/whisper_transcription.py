"""Whisper transcription adapters: in-process tiny and CLI small."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import wave
from typing import Any

import numpy as np

from hey_clever.config.settings import TranscriptionConfig
from hey_clever.ports.transcription import ITranscription

log = logging.getLogger(__name__)


class WhisperTinyTranscription(ITranscription):
    """In-process faster-whisper tiny model for fast keyword detection."""

    def __init__(self, model: Any | None = None) -> None:
        if model is not None:
            self._model = model
        else:
            from faster_whisper import WhisperModel

            self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
            log.info("Whisper tiny model loaded")

    def transcribe(self, audio: np.ndarray) -> str:
        audio_f32 = audio.astype(np.float32) / 32767.0
        try:
            segments, _info = self._model.transcribe(
                audio_f32,
                beam_size=1,
                best_of=1,
                language=None,
                vad_filter=False,
            )
            return " ".join(seg.text for seg in segments).strip()
        except Exception as e:
            log.error("Whisper tiny transcription failed: %s", e)
            return ""


class WhisperCLITranscription(ITranscription):
    """CLI-based Whisper small model for high-quality command transcription."""

    def __init__(self, config: TranscriptionConfig) -> None:
        self._config = config

    def transcribe(self, audio: np.ndarray) -> str:
        wav_path = self._save_wav(audio)
        try:
            result = subprocess.run(
                [
                    self._config.whisper_bin,
                    wav_path,
                    "--model",
                    self._config.command_model,
                    "--language",
                    self._config.language,
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
            log.warning("Whisper txt output not found, using stdout")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            log.error("Whisper CLI timed out")
            return ""
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)

    @staticmethod
    def _save_wav(audio: np.ndarray, sample_rate: int = 16000) -> str:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
        return path
