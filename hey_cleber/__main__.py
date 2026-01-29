"""Entry point for Hey Cleber voice assistant.

Usage:
    python -m hey_cleber [--debug] [--device N] [--keywords word1,word2]
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time

import numpy as np
import sounddevice as sd

from .audio import play_beep, record_until_silence
from .config import AppConfig, parse_args
from .gateway import send_to_clawdbot
from .keywords import check_keyword
from .transcription import transcribe_full, transcribe_tiny
from .tts import tts_and_play
from .vad import SileroVAD, find_silero_vad_model

log = logging.getLogger("hey-cleber")


def main(config: AppConfig | None = None) -> None:
    """Run the Hey Cleber voice assistant main loop."""
    if config is None:
        config = parse_args()

    # Ensure PipeWire access
    os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")

    logging.basicConfig(
        level=logging.DEBUG if config.debug else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    log.info("Activation keywords: %s", list(config.keywords))

    # Initialize Silero VAD
    vad_model_path = find_silero_vad_model()
    log.info("Loading Silero VAD from: %s", vad_model_path)
    vad = SileroVAD(vad_model_path, threshold=config.vad_threshold)

    # Initialize faster-whisper tiny model for keyword detection
    log.info("Loading Whisper tiny model for keyword detection...")
    from faster_whisper import WhisperModel
    whisper_tiny = WhisperModel("tiny", device="cpu", compute_type="int8")
    log.info("Whisper tiny model loaded.")

    log.info(
        "Starting audio stream (sample_rate=%d, block_size=%d)",
        config.sample_rate, config.block_size,
    )

    # Shared state
    audio_q: queue.Queue[np.ndarray] = queue.Queue()
    is_speaking = threading.Event()

    def audio_callback(
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            log.debug("Audio status: %s", status)
        if is_speaking.is_set():
            return
        block = (indata[:, 0] * 32767).astype(np.int16)
        audio_q.put(block)

    device_kwargs: dict = {}
    if config.device is not None:
        device_kwargs["device"] = config.device

    stream = sd.InputStream(
        samplerate=config.sample_rate,
        channels=config.channels,
        blocksize=config.block_size,
        dtype="float32",
        callback=audio_callback,
        **device_kwargs,
    )

    log.info("=== Hey Cleber is listening! Say 'Cleber' to activate. ===")

    with stream:
        while True:
            # -----------------------------------------------------------
            # Phase 1: VAD + keyword detection
            # -----------------------------------------------------------
            speech_buffer: list[np.ndarray] = []
            in_speech = False
            silence_after_speech_start: float | None = None
            buffer_duration = 0.0

            while True:
                try:
                    block = audio_q.get(timeout=1.0)
                except queue.Empty:
                    continue

                is_speech = vad.is_speech(block)
                block_dur = len(block) / config.sample_rate

                if is_speech:
                    if not in_speech:
                        in_speech = True
                        log.debug("VAD: speech started")
                    silence_after_speech_start = None
                    speech_buffer.append(block)
                    buffer_duration += block_dur

                    if buffer_duration > config.max_keyword_buffer_sec:
                        log.debug("Keyword buffer full (%.1fs), checking...", buffer_duration)
                        break
                else:
                    if in_speech:
                        speech_buffer.append(block)
                        buffer_duration += block_dur

                        if silence_after_speech_start is None:
                            silence_after_speech_start = time.monotonic()
                        elif (
                            time.monotonic() - silence_after_speech_start
                            >= config.keyword_silence_sec
                        ):
                            log.debug("VAD: speech ended (%.1fs buffered)", buffer_duration)
                            break

            # Check if we have enough speech
            if buffer_duration < config.min_keyword_speech_sec:
                log.debug("Speech too short (%.2fs), ignoring", buffer_duration)
                vad.reset()
                continue

            # Transcribe with Whisper tiny
            audio_chunk = np.concatenate(speech_buffer)
            log.debug("Transcribing %.1fs of speech with Whisper tiny...", buffer_duration)
            text = transcribe_tiny(whisper_tiny, audio_chunk)
            log.debug("Whisper tiny heard: '%s'", text)

            # Check for keyword
            if not check_keyword(text, config.keywords):
                log.debug("No keyword found, continuing to listen")
                vad.reset()
                continue

            log.info("🎤 Keyword detected in: '%s'", text)
            vad.reset()

            # -----------------------------------------------------------
            # Phase 2: Record command, transcribe, send to Clawdbot
            # -----------------------------------------------------------

            # Play beep (mute mic to avoid capturing beep)
            is_speaking.set()
            play_beep(sample_rate=config.sample_rate)
            is_speaking.clear()

            # Drain queue (discard stale audio)
            while not audio_q.empty():
                try:
                    audio_q.get_nowait()
                except queue.Empty:
                    break

            # Record until silence
            log.info("Recording command...")
            audio = record_until_silence(audio_q, config)

            if audio is None or len(audio) == 0:
                log.info("No speech captured, returning to listening")
                continue

            duration = len(audio) / config.sample_rate
            log.info("Recorded %.1fs of audio, transcribing with Whisper small...", duration)

            # Transcribe with Whisper small (full quality)
            text = transcribe_full(audio, config)
            if not text:
                log.info("Empty transcription, returning to listening")
                continue

            log.info("Transcribed: '%s'", text)

            # Send to Clawdbot
            log.info("Sending to Clawdbot...")
            response = send_to_clawdbot(text, config)
            log.info("Response: '%s'", response[:200])

            # TTS and play
            tts_and_play(response, config, audio_q=audio_q, speaking_flag=is_speaking)

            log.info("=== Ready for next keyword ===")


if __name__ == "__main__":
    main()
