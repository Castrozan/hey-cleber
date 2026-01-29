"""Configuration constants and CLI argument parsing."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

# Audio constants
SAMPLE_RATE: int = 16000
CHANNELS: int = 1
BLOCK_SIZE: int = 512  # Silero VAD expects 512 samples at 16 kHz (32ms)

# Silence detection for post-keyword recording (Phase 2)
DEFAULT_SILENCE_THRESHOLD_RMS: float = 300.0
DEFAULT_SILENCE_DURATION_SEC: float = 2.0
MAX_RECORDING_SEC: float = 30.0
MIN_RECORDING_SEC: float = 0.5

# VAD + keyword detection settings (Phase 1)
DEFAULT_VAD_THRESHOLD: float = 0.4
MAX_KEYWORD_BUFFER_SEC: float = 5.0
KEYWORD_SILENCE_SEC: float = 0.8
MIN_KEYWORD_SPEECH_SEC: float = 0.3

# Default keywords and phonetic variants
DEFAULT_KEYWORDS: list[str] = [
    "cleber", "kleber", "clever", "cleaver", "clebert", "cleber's",
    "kleiber", "klebber", "cleyber", "klever",
]

# External binary paths
DEFAULT_WHISPER_BIN: str = "/run/current-system/sw/bin/whisper"
DEFAULT_MPV_BIN: str = "/run/current-system/sw/bin/mpv"

# Gateway defaults
DEFAULT_GATEWAY_URL: str = "http://localhost:18789"
DEFAULT_GATEWAY_TOKEN: str = ""  # Set via CLAWDBOT_GATEWAY_TOKEN env var


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    # Audio
    sample_rate: int = SAMPLE_RATE
    channels: int = CHANNELS
    block_size: int = BLOCK_SIZE

    # Recording
    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD_RMS
    silence_duration: float = DEFAULT_SILENCE_DURATION_SEC
    max_recording_sec: float = MAX_RECORDING_SEC
    min_recording_sec: float = MIN_RECORDING_SEC

    # VAD
    vad_threshold: float = DEFAULT_VAD_THRESHOLD
    max_keyword_buffer_sec: float = MAX_KEYWORD_BUFFER_SEC
    keyword_silence_sec: float = KEYWORD_SILENCE_SEC
    min_keyword_speech_sec: float = MIN_KEYWORD_SPEECH_SEC

    # Keywords
    keywords: tuple[str, ...] = tuple(DEFAULT_KEYWORDS)

    # Paths
    whisper_bin: str = DEFAULT_WHISPER_BIN
    mpv_bin: str = DEFAULT_MPV_BIN

    # Gateway
    gateway_url: str = DEFAULT_GATEWAY_URL
    gateway_token: str = DEFAULT_GATEWAY_TOKEN

    # Runtime
    device: int | None = None
    debug: bool = False


def parse_args(argv: list[str] | None = None) -> AppConfig:
    """Parse CLI arguments and environment variables into an AppConfig."""
    parser = argparse.ArgumentParser(description="Hey Cleber voice assistant")
    parser.add_argument(
        "--list-devices", action="store_true",
        help="List audio devices and exit",
    )
    parser.add_argument(
        "--device", type=int, default=None,
        help="Input device index",
    )
    parser.add_argument(
        "--silence-threshold", type=float,
        default=DEFAULT_SILENCE_THRESHOLD_RMS,
        help="RMS silence threshold for command recording (default: %(default)s)",
    )
    parser.add_argument(
        "--keywords", type=str, default=None,
        help="Comma-separated activation keywords (default: cleber variants)",
    )
    parser.add_argument(
        "--vad-threshold", type=float, default=DEFAULT_VAD_THRESHOLD,
        help="Silero VAD speech probability threshold (default: %(default)s)",
    )
    parser.add_argument("--debug", action="store_true")
    # Legacy args (ignored, kept for backward compat)
    parser.add_argument("--wake-word", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--threshold", type=float, default=None, help=argparse.SUPPRESS)

    args = parser.parse_args(argv)

    if args.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        raise SystemExit(0)

    keywords: tuple[str, ...]
    if args.keywords:
        keywords = tuple(k.strip() for k in args.keywords.split(",") if k.strip())
    else:
        keywords = tuple(DEFAULT_KEYWORDS)

    return AppConfig(
        silence_threshold=args.silence_threshold,
        vad_threshold=args.vad_threshold,
        keywords=keywords,
        whisper_bin=os.environ.get("WHISPER_BIN", DEFAULT_WHISPER_BIN),
        mpv_bin=os.environ.get("MPV_BIN", DEFAULT_MPV_BIN),
        gateway_url=os.environ.get("CLAWDBOT_GATEWAY_URL", DEFAULT_GATEWAY_URL),
        gateway_token=os.environ.get("CLAWDBOT_GATEWAY_TOKEN", DEFAULT_GATEWAY_TOKEN),
        device=args.device,
        debug=args.debug,
    )
