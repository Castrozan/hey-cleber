"""Settings dataclass with nested sub-configs for hey-clever."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    block_size: int = 512
    device: int | None = None


@dataclass(frozen=True)
class VADConfig:
    threshold: float = 0.4
    silence_duration: float = 0.8
    min_speech_duration: float = 0.3
    max_buffer_sec: float = 5.0


@dataclass(frozen=True)
class RecordingConfig:
    silence_threshold: float = 300.0
    silence_duration: float = 2.0
    max_duration: float = 30.0
    min_duration: float = 0.5


@dataclass(frozen=True)
class KeywordConfig:
    keywords: tuple[str, ...] = (
        "clever",
        "klever",
        "cleber",
        "kleber",
        "cleaver",
        "clevert",
        "kleiber",
        "klebber",
        "cleyber",
        "cleber's",
    )


@dataclass(frozen=True)
class TranscriptionConfig:
    keyword_model: str = "tiny"
    command_model: str = "small"
    whisper_bin: str = "/run/current-system/sw/bin/whisper"
    language: str = "en"


@dataclass(frozen=True)
class GatewayConfig:
    url: str = "http://localhost:18789"
    token: str = ""
    timeout: int = 60


@dataclass(frozen=True)
class TTSConfig:
    voice: str = "en-US-GuyNeural"
    mpv_bin: str = "/run/current-system/sw/bin/mpv"


@dataclass(frozen=True)
class Settings:
    audio: AudioConfig = field(default_factory=AudioConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    recording: RecordingConfig = field(default_factory=RecordingConfig)
    keyword: KeywordConfig = field(default_factory=KeywordConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    debug: bool = False

    @classmethod
    def from_args(cls, argv: list[str] | None = None) -> Settings:
        parser = argparse.ArgumentParser(description="Hey Clever voice assistant")
        parser.add_argument(
            "--list-devices",
            action="store_true",
            help="List audio devices and exit",
        )
        parser.add_argument(
            "--device",
            type=int,
            default=None,
            help="Input device index",
        )
        parser.add_argument(
            "--silence-threshold",
            type=float,
            default=RecordingConfig.silence_threshold,
            help="RMS silence threshold for command recording (default: %(default)s)",
        )
        parser.add_argument(
            "--keywords",
            type=str,
            default=None,
            help="Comma-separated activation keywords (default: clever variants)",
        )
        parser.add_argument(
            "--vad-threshold",
            type=float,
            default=VADConfig.threshold,
            help="Silero VAD speech probability threshold (default: %(default)s)",
        )
        parser.add_argument("--debug", action="store_true")
        # Legacy args (suppressed, kept for backward compat)
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
            keywords = KeywordConfig.keywords

        return cls(
            audio=AudioConfig(device=args.device),
            vad=VADConfig(threshold=args.vad_threshold),
            recording=RecordingConfig(silence_threshold=args.silence_threshold),
            keyword=KeywordConfig(keywords=keywords),
            transcription=TranscriptionConfig(
                whisper_bin=os.environ.get("WHISPER_BIN", TranscriptionConfig.whisper_bin),
            ),
            gateway=GatewayConfig(
                url=os.environ.get("CLAWDBOT_GATEWAY_URL", GatewayConfig.url),
                token=os.environ.get("CLAWDBOT_GATEWAY_TOKEN", GatewayConfig.token),
            ),
            tts=TTSConfig(
                mpv_bin=os.environ.get("MPV_BIN", TTSConfig.mpv_bin),
            ),
            debug=args.debug,
        )

    @classmethod
    def default(cls) -> Settings:
        return cls()
