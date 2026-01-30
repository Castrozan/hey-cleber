# Hey Clever

Always-on voice assistant powered by [Clawdbot](https://github.com/clawdbot/clawdbot).

Listens for your wake word, records your command, transcribes it, sends it to your Clawdbot agent, and speaks the response back — all locally.

## How it works

**Phase 1 — Keyword Listening** (lightweight, always running):
1. **Silero VAD** detects speech segments from the microphone
2. Buffers speech (up to 5 seconds)
3. **faster-whisper tiny** model transcribes the buffer (fast, in-process)
4. Checks for activation keywords (e.g. "clever", "hey clever")
5. No match → discard, keep listening

**Phase 2 — Command** (triggered on keyword):
1. Beep → Record until silence (2s silence, 30s max)
2. Transcribe with **Whisper small** (CLI, higher quality)
3. Send to Clawdbot gateway via OpenAI-compatible `/v1/chat/completions` endpoint
4. TTS response via **edge-tts** (Microsoft Edge, free)
5. Playback via **mpv** over PipeWire
6. Return to Phase 1

## Architecture

Hexagonal architecture (ports & adapters):

```
hey_clever/
├── ports/               # ABC interfaces
├── domain/              # State machine, VAD, audio buffer
├── adapters/            # SoundDevice, Whisper, Clawdbot, EdgeTTS, etc.
├── config/              # Settings, logging
├── factory.py           # Wires adapters into domain
├── __main__.py          # Entry point
├── audio.py             # Audio utilities
├── vad.py               # Silero VAD wrapper
├── transcription.py     # Whisper transcription
├── gateway.py           # Clawdbot client
├── tts.py               # TTS + playback
├── keywords.py          # Keyword matching
tests/
├── conftest.py          # Shared fixtures
├── test_*.py            # Comprehensive test suite
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
hey-clever.url = "github:castrozan/hey-clever";
```

Enable via Home Manager:

```nix
imports = [ inputs.hey-clever.homeManagerModules.default ];

services.hey-clever = {
  enable = true;
  gatewayUrl = "http://localhost:18789";
};
```

The flake manages the venv, dependencies, and systemd service automatically.

### Manual setup

```bash
python3 -m venv ~/.local/share/hey-clever-venv
source ~/.local/share/hey-clever-venv/bin/activate
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
source ~/.local/share/hey-clever-venv/bin/activate
python3 -m hey_clever
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--keywords` | clever,klever,cleber,... | Comma-separated activation keywords |
| `--vad-threshold` | 0.4 | Silero VAD speech detection threshold |
| `--silence-threshold` | 300 | RMS silence threshold for recording |
| `--device` | (default) | Input audio device index |
| `--list-devices` | | List available audio devices and exit |
| `--debug` | | Enable debug logging |

### Systemd service

```bash
systemctl --user status hey-clever
systemctl --user restart hey-clever
journalctl --user -u hey-clever -f
```

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAWDBOT_GATEWAY_URL` | `http://localhost:18789` | Clawdbot gateway URL |
| `CLAWDBOT_GATEWAY_TOKEN` | *(required)* | Gateway auth token |
| `WHISPER_BIN` | `/run/current-system/sw/bin/whisper` | Path to Whisper CLI |
| `MPV_BIN` | `/run/current-system/sw/bin/mpv` | Path to mpv |

## Development

### Using devenv (recommended)

```bash
# Enter the dev shell (Python 3.12, all deps, tools)
devenv shell

# Run convenience scripts inside the shell
test       # pytest
lint       # ruff check
format     # ruff format
typecheck  # mypy
check      # all of the above
run        # python -m hey_clever
```

Or run directly without entering the shell:

```bash
devenv shell -- check
devenv shell -- test
```

### Using Make

```bash
make check      # lint + test
make test       # pytest
make lint       # ruff check
make format     # ruff format
```

### Manual setup

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## License

MIT
