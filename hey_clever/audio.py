"""Audio helpers: RMS, beep generation, playback, WAV saving, recording."""

from __future__ import annotations

import logging
import os
import queue
import subprocess
import threading
import time
import wave

import numpy as np
import sounddevice as sd

from .config import CHANNELS, SAMPLE_RATE, AppConfig

log = logging.getLogger("hey-clever.audio")


def rms(block: np.ndarray) -> float:
    """Root mean square of an audio block."""
    return float(np.sqrt(np.mean(block.astype(np.float64) ** 2)))


def generate_beep(
    freq: float = 880.0,
    duration: float = 0.15,
    sample_rate: int = SAMPLE_RATE,
    volume: float = 0.3,
) -> np.ndarray:
    """Generate a short beep as int16 numpy array."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return (volume * 32767 * np.sin(2 * np.pi * freq * t)).astype(np.int16)


def play_beep(sample_rate: int = SAMPLE_RATE) -> None:
    """Play a short beep to indicate keyword detected."""
    try:
        beep = generate_beep(sample_rate=sample_rate)
        sd.play(beep, samplerate=sample_rate, blocksize=4096)
        sd.wait()
    except Exception as e:
        log.warning("Could not play beep: %s", e)


def play_audio_file(
    path: str,
    mpv_bin: str,
    interrupt_event: threading.Event | None = None,
) -> bool:
    """Play an audio file via mpv over PipeWire.

    Returns True if playback was interrupted, False otherwise.
    """
    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = env.get("XDG_RUNTIME_DIR", "/run/user/1000")
    try:
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
        proc = subprocess.Popen(
            [mpv_bin, "--no-video", "--ao=pipewire", path],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        while proc.poll() is None:
            if interrupt_event is not None and interrupt_event.is_set():
                log.info("⚡ Playback interrupted — killing mpv")
                proc.kill()
                proc.wait(timeout=5)
                return True
            time.sleep(0.05)
        return False
    except Exception as e:
        log.error("Audio playback failed: %s", e)
        return False


def save_wav(
    audio_data: np.ndarray,
    path: str,
    channels: int = CHANNELS,
    sample_rate: int = SAMPLE_RATE,
) -> None:
    """Save int16 numpy array as WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())


def record_until_silence(
    audio_queue: queue.Queue[np.ndarray],
    config: AppConfig,
) -> np.ndarray | None:
    """Record from the audio queue until silence is detected.

    Returns the recorded audio as int16 numpy array, or None if too short / no speech.
    """
    frames: list[np.ndarray] = []
    silence_start: float | None = None
    recording_start = time.monotonic()
    got_speech = False

    while True:
        try:
            block = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        frames.append(block)
        elapsed = time.monotonic() - recording_start
        block_rms = rms(block)

        if block_rms > config.silence_threshold:
            got_speech = True
            silence_start = None
        else:
            if got_speech and silence_start is None:
                silence_start = time.monotonic()

        if elapsed >= config.max_recording_sec:
            log.info("Max recording duration reached (%.0fs)", config.max_recording_sec)
            break

        if got_speech and silence_start is not None:
            if time.monotonic() - silence_start >= config.silence_duration:
                log.info("Silence detected after %.1fs of recording", elapsed)
                break

    if not frames:
        return None

    audio = np.concatenate(frames)
    duration = len(audio) / config.sample_rate

    if duration < config.min_recording_sec or not got_speech:
        log.info("Recording too short or no speech (%.2fs)", duration)
        return None

    return audio
