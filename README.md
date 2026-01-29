# Hey Cleber 🎤

Always-on voice assistant powered by [Clawdbot](https://github.com/clawdbot/clawdbot).

Listens for your wake word, records your command, transcribes it, sends it to your Clawdbot agent, and speaks the response back — all locally.

## How it works

**Phase 1 — Keyword Listening** (lightweight, always running):
1. **Silero VAD** detects speech segments from the microphone
2. Buffers speech (up to 5 seconds)
3. **faster-whisper tiny** model transcribes the buffer (fast, in-process)
4. Checks for activation keywords (e.g. "cleber", "hey cleber", "hello cleber")
5. No match → discard, keep listening

**Phase 2 — Command** (triggered on keyword):
1. Beep → Record until silence (2s silence, 30s max)
2. Transcribe with **Whisper small** (CLI, higher quality)
3. Send to Clawdbot gateway via OpenAI-compatible `/v1/chat/completions` endpoint
4. TTS response via **edge-tts** (Microsoft Edge, free)
5. Playback via **mpv** over PipeWire
6. Return to Phase 1

## Package structure

```
hey_cleber/
├── __init__.py          # Package version
├── __main__.py          # Entry point and main loop
├── audio.py             # Audio helpers (RMS, beep, play, save WAV, record)
├── vad.py               # Silero VAD wrapper class
├── transcription.py     # Whisper tiny + Whisper CLI transcription
├── gateway.py           # Clawdbot gateway client
├── tts.py               # TTS generation + playback (edge-tts + mpv)
├── config.py            # Configuration constants and CLI args
├── keywords.py          # Keyword matching logic
tests/
├── test_keywords.py     # Keyword matching tests
├── test_config.py       # Config/args tests
├── test_audio.py        # RMS, beep generation tests
├── test_transcription.py # Transcription tests (mocked)
```

## Requirements

- Python 3.10+
- Linux with PipeWire audio
- [Clawdbot](https://github.com/clawdbot/clawdbot) gateway running with `chatCompletions` endpoint enabled
- [Whisper](https://github.com/openai/whisper) CLI installed (for command transcription)
- `mpv` for audio playback

### Python dependencies

- `sounddevice`
- `numpy`
- `requests`
- `faster-whisper`
- `onnxruntime`
- `edge-tts`
- `openwakeword` (for bundled Silero VAD model)

## Setup (NixOS)

Add to your flake inputs:

```nix
hey-cleber.url = "github:castrozan/hey-cleber/v2.0.0";
```

Enable via Home Manager:

```nix
imports = [ inputs.hey-cleber.homeManagerModules.default ];

services.hey-cleber = {
  enable = true;
  gatewayUrl = "http://localhost:18789";
};
```

The flake manages the venv, dependencies, and systemd service automatically.

### Manual setup

```bash
python3 -m venv ~/.local/share/hey-cleber-venv
source ~/.local/share/hey-cleber-venv/bin/activate
pip install sounddevice numpy requests faster-whisper onnxruntime edge-tts openwakeword
```

### Clawdbot config

Enable the chat completions endpoint in your `clawdbot.json`:

```json
{
  "gateway": {
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    }
  }
}
```

## Usage

```bash
source ~/.local/share/hey-cleber-venv/bin/activate
python3 -m hey_cleber
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--keywords` | cleber,kleber,clever,... | Comma-separated activation keywords |
| `--vad-threshold` | 0.4 | Silero VAD speech detection threshold |
| `--silence-threshold` | 300 | RMS silence threshold for recording |
| `--device` | (default) | Input audio device index |
| `--list-devices` | | List available audio devices and exit |
| `--debug` | | Enable debug logging |

### Systemd service

```bash
systemctl --user status hey-cleber
systemctl --user restart hey-cleber
journalctl --user -u hey-cleber -f
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWDBOT_GATEWAY_URL` | `http://localhost:18789` | Clawdbot gateway URL |
| `CLAWDBOT_GATEWAY_TOKEN` | *(required)* | Gateway auth token |
| `WHISPER_BIN` | `/run/current-system/sw/bin/whisper` | Path to Whisper CLI |
| `MPV_BIN` | `/run/current-system/sw/bin/mpv` | Path to mpv |

## Development

```bash
# Run all checks (lint + typecheck + tests)
make check

# Individual targets
make test       # pytest
make lint       # ruff check
make format     # ruff format
make typecheck  # mypy
```

### Running tests

```bash
pip install pytest ruff mypy
python -m pytest tests/ -v
```

## License

MIT
