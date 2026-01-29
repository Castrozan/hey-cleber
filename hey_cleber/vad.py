"""Silero VAD (Voice Activity Detection) wrapper using ONNX runtime."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import onnxruntime

from .config import SAMPLE_RATE


class SileroVAD:
    """Silero VAD using ONNX runtime (no torch needed)."""

    def __init__(self, model_path: str, threshold: float = 0.4) -> None:
        self.threshold = threshold
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = onnxruntime.InferenceSession(model_path, sess_options=opts)
        self.reset()

    def reset(self) -> None:
        """Reset internal LSTM state."""
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self._sr = np.array(SAMPLE_RATE, dtype=np.int64)

    def __call__(self, audio_chunk: np.ndarray) -> float:
        """Run VAD on a chunk of audio (int16 or float32). Returns speech probability."""
        if audio_chunk.dtype == np.int16:
            audio = audio_chunk.astype(np.float32) / 32767.0
        else:
            audio = audio_chunk.astype(np.float32)

        audio = audio.reshape(1, -1)

        ort_inputs = {
            "input": audio,
            "h": self._h,
            "c": self._c,
            "sr": self._sr,
        }
        out, h_new, c_new = self.session.run(None, ort_inputs)
        self._h = h_new
        self._c = c_new

        return float(out[0][0])

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Returns True if the audio chunk is classified as speech."""
        return self(audio_chunk) >= self.threshold


def find_silero_vad_model() -> str:
    """Find the Silero VAD ONNX model bundled with openwakeword.

    Raises:
        FileNotFoundError: If model file cannot be found.
    """
    # Check openwakeword package first
    try:
        import openwakeword
        pkg_dir = os.path.dirname(openwakeword.__file__)
        path = os.path.join(pkg_dir, "resources", "models", "silero_vad.onnx")
        if os.path.exists(path):
            return path
    except ImportError:
        pass

    # Fallback: search in venv
    venv = Path(sys.prefix)
    for p in venv.rglob("silero_vad.onnx"):
        return str(p)

    raise FileNotFoundError(
        "silero_vad.onnx not found. Install openwakeword or provide the model."
    )
