"""Edge TTS adapter with mpv playback over PipeWire."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import time

from hey_clever.config.settings import TTSConfig
from hey_clever.ports.tts import ITTS

log = logging.getLogger(__name__)


class EdgeTTSAdapter(ITTS):
    def __init__(self, config: TTSConfig) -> None:
        self._config = config
        self._speaking = False

    def speak(self, text: str) -> bool:
        mp3_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                mp3_path = f.name

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "edge_tts",
                    "--text",
                    text,
                    "--voice",
                    self._config.voice,
                    "--write-media",
                    mp3_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if (
                result.returncode == 0
                and os.path.exists(mp3_path)
                and os.path.getsize(mp3_path) > 0
            ):
                self._speaking = True
                try:
                    self._play_audio(mp3_path)
                finally:
                    self._speaking = False
                return False
        except Exception as e:
            log.warning("edge-tts failed: %s", e)
        finally:
            if mp3_path and os.path.exists(mp3_path):
                os.unlink(mp3_path)

        self._fallback_espeak(text)
        return False

    def stop(self) -> None:
        self._speaking = False

    def is_speaking(self) -> bool:
        return self._speaking

    def _play_audio(self, path: str) -> None:
        env = os.environ.copy()
        env.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
        subprocess.run(
            ["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"],
            env=env,
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            ["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "1.0"],
            env=env,
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            [self._config.mpv_bin, "--no-video", "--ao=pipewire", path],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.3)

    @staticmethod
    def _fallback_espeak(text: str) -> None:
        try:
            subprocess.run(
                ["espeak-ng", "-s", "150", text],
                capture_output=True,
                timeout=30,
                env={**os.environ, "XDG_RUNTIME_DIR": "/run/user/1000"},
            )
        except Exception:
            log.warning("No TTS backend available")
