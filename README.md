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

## Setup

### Quick setup (NixOS)

```bash
chmod +x hey-cleber-setup.sh
./hey-cleber-setup.sh
```

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
python3 hey-cleber.py
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--keywords` | cleber,kleber,clever,... | Comma-separated activation keywords |
| `--vad-threshold` | 0.5 | Silero VAD speech detection threshold |
| `--silence-threshold` | 300 | RMS silence threshold for recording |
| `--device` | (default) | Input audio device index |
| `--list-devices` | | List available audio devices and exit |
| `--debug` | | Enable debug logging |

### Systemd service

```bash
# Install as user service
cp hey-cleber.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now hey-cleber

# Manage
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

## License

MIT
