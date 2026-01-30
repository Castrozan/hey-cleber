"""Entry point: wire adapters to ports and start the voice detector."""

from __future__ import annotations

import logging
import os

from hey_clever.adapters.beep_sound_cues import BeepSoundCues
from hey_clever.adapters.clawdbot_gateway import ClawdbotGateway
from hey_clever.adapters.edge_tts_adapter import EdgeTTSAdapter
from hey_clever.adapters.keyword_adapter import KeywordAdapter
from hey_clever.adapters.sounddevice_input import SoundDeviceInput
from hey_clever.adapters.whisper_transcription import (
    WhisperCLITranscription,
    WhisperTinyTranscription,
)
from hey_clever.config.logging_config import setup_logging
from hey_clever.config.settings import Settings
from hey_clever.domain.vad import SileroVAD, find_silero_vad_model
from hey_clever.domain.voice_detector import VoiceDetector

log = logging.getLogger(__name__)


def main(settings: Settings | None = None) -> None:
    if settings is None:
        settings = Settings.from_args()

    os.environ.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
    setup_logging(settings.debug)

    log.info("Activation keywords: %s", list(settings.keyword.keywords))

    vad_model_path = find_silero_vad_model()
    log.info("Loading Silero VAD from: %s", vad_model_path)
    vad = SileroVAD(vad_model_path, threshold=settings.vad.threshold)

    audio_input = SoundDeviceInput(settings.audio)
    keyword_transcription = WhisperTinyTranscription()
    command_transcription = WhisperCLITranscription(settings.transcription)
    keyword_detector = KeywordAdapter(settings.keyword)
    gateway = ClawdbotGateway(settings.gateway)
    tts = EdgeTTSAdapter(settings.tts)
    sound_cues = BeepSoundCues()

    detector = VoiceDetector(
        audio_input=audio_input,
        vad=vad,
        keyword_transcription=keyword_transcription,
        command_transcription=command_transcription,
        keyword_detector=keyword_detector,
        gateway=gateway,
        tts=tts,
        sound_cues=sound_cues,
        settings=settings,
    )

    detector.start()


if __name__ == "__main__":
    main()
