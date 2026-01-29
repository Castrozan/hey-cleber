"""Text-to-speech synthesis and playback."""

from __future__ import annotations

import logging
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time

from .audio import play_audio_file
from .config import AppConfig

log = logging.getLogger("hey-cleber.tts")


def tts_and_play(
    text: str,
    config: AppConfig,
    audio_q: queue.Queue | None = None,
    speaking_flag: threading.Event | None = None,
) -> bool:
    """Convert text to speech and play it.

    Args:
        text: Text to speak.
        config: Application configuration.
        audio_q: Audio queue to drain after playback.
        speaking_flag: Event to signal mic muting during playback.

    Returns:
        True if playback was interrupted, False otherwise.
    """
    mp3_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_path = f.name

        result = subprocess.run(
            [
                sys.executable, "-m", "edge_tts",
                "--text", text,
                "--voice", "en-US-GuyNeural",
                "--write-media", mp3_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            log.info("Playing TTS response via edge-tts")

            if speaking_flag is not None:
                speaking_flag.set()
                log.info("🔇 Mic muted during TTS playback")

            try:
                play_audio_file(mp3_path, mpv_bin=config.mpv_bin)
            finally:
                if speaking_flag is not None:
                    time.sleep(0.5)
                    speaking_flag.clear()
                    if audio_q is not None:
                        while not audio_q.empty():
                            try:
                                audio_q.get_nowait()
                            except queue.Empty:
                                break
                    log.info("🔊 Mic re-enabled")

            return False
    except Exception as e:
        log.warning("edge-tts failed: %s, trying fallback", e)
    finally:
        if mp3_path and os.path.exists(mp3_path):
            os.unlink(mp3_path)

    # Fallback: espeak-ng
    try:
        subprocess.run(
            ["espeak-ng", "-s", "150", text],
            capture_output=True,
            timeout=30,
            env={**os.environ, "XDG_RUNTIME_DIR": "/run/user/1000"},
        )
    except Exception:
        log.warning("No TTS backend available. Response text: %s", text)

    return False
