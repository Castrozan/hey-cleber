# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Hey Clever is an always-on voice assistant for Linux/NixOS. It listens for a wake word via Silero VAD + Whisper tiny, then captures commands, transcribes with Whisper small, sends to a Clawdbot gateway (OpenAI-compatible API), and speaks responses via edge-tts + mpv over PipeWire.

## Development Environment

Uses devenv (Nix-based). Enter with `devenv shell`. Do NOT use direnv.

## Commands

All available via devenv scripts or Makefile:

- **Run**: `run` or `run --debug` (inside devenv shell)
- **Test**: `make test` or `pytest tests/ -v`
- **Single test**: `pytest tests/test_keywords.py -v` or `pytest tests/test_keywords.py::test_name -v`
- **Lint**: `make lint` or `ruff check hey_clever/ tests/`
- **Format**: `make format` or `ruff format hey_clever/ tests/`
- **Type check**: `make typecheck` or `mypy hey_clever/ --ignore-missing-imports`
- **All checks**: `make check` (lint + typecheck + test)

## Architecture

Hexagonal architecture (ports & adapters) with state machine orchestration.

### Layers

- **Ports** (`hey_clever/ports/`): ABC interfaces for all external dependencies
- **Domain** (`hey_clever/domain/`): State machine (DetectorState), VoiceDetector orchestrator, AudioBuffer
- **Adapters** (`hey_clever/adapters/`): Concrete implementations (SoundDevice, WhisperTiny, WhisperCLI, Clawdbot, EdgeTTS, Keyword, BeepSoundCues)
- **Config** (`hey_clever/config/`): Settings dataclass with sub-configs, logging setup

### State Machine Flow

```
IDLE → (VAD speech) → LISTENING → (silence) → check keyword
  → keyword found → ACTIVATED → (record until silence) → PROCESSING → (gateway) → RESPONDING → IDLE
  → no keyword → IDLE
```

### Sound Cues

Distinct audio cues at each state transition:
- Keyword detected: 880Hz beep
- Recording done: 440Hz tone
- Processing: 660Hz double blip
- Response ready: ascending tone

Audio runs at 16kHz mono, 512-sample blocks. Mic muting via adapter prevents feedback during beep/TTS playback.

## Module Responsibilities

- **config/settings.py** — Settings dataclass with sub-configs from CLI args + env vars
- **domain/voice_detector.py** — State machine orchestrator injecting all ports
- **domain/vad.py** — Silero VAD ONNX wrapper with stateful LSTM hidden states
- **domain/audio_buffer.py** — Numpy deque buffer with max duration eviction
- **adapters/** — Concrete implementations of all port interfaces

## Configuration

Key env vars: `CLAWDBOT_GATEWAY_TOKEN` (required), `CLAWDBOT_GATEWAY_URL`, `WHISPER_BIN`, `MPV_BIN`.

CLI flags: `--keywords`, `--vad-threshold`, `--silence-threshold`, `--device`, `--debug`.

NixOS deployment via Home Manager module in `flake.nix`.

## Code Style

- Python 3.10+ target, developed with 3.12
- Ruff: line length 100, rules E/F/W/I/N/UP
- Mypy with strict-ish settings
- Pre-commit hooks run ruff on commit
