"""Voice detection orchestrator — state machine driving all ports."""

from __future__ import annotations

import logging
import time

import numpy as np

from hey_clever.config.settings import Settings
from hey_clever.domain.audio_buffer import AudioBuffer
from hey_clever.domain.detector_state import DetectorState
from hey_clever.domain.vad import SileroVAD
from hey_clever.ports.audio_input import IAudioInput
from hey_clever.ports.gateway import IGateway
from hey_clever.ports.keyword_detection import IKeywordDetector
from hey_clever.ports.sound_cues import ISoundCues
from hey_clever.ports.transcription import ITranscription
from hey_clever.ports.tts import ITTS

log = logging.getLogger(__name__)


def _rms(block: np.ndarray) -> float:
    return float(np.sqrt(np.mean(block.astype(np.float64) ** 2)))


class VoiceDetector:
    """Orchestrates the IDLE → LISTENING → ACTIVATED → PROCESSING → RESPONDING loop."""

    def __init__(
        self,
        audio_input: IAudioInput,
        vad: SileroVAD,
        keyword_transcription: ITranscription,
        command_transcription: ITranscription,
        keyword_detector: IKeywordDetector,
        gateway: IGateway,
        tts: ITTS,
        sound_cues: ISoundCues,
        settings: Settings,
    ) -> None:
        self._audio = audio_input
        self._vad = vad
        self._kw_transcription = keyword_transcription
        self._cmd_transcription = command_transcription
        self._keyword = keyword_detector
        self._gateway = gateway
        self._tts = tts
        self._cues = sound_cues
        self._settings = settings

        self._kw_buffer = AudioBuffer(
            max_duration=settings.vad.max_buffer_sec,
            sample_rate=settings.audio.sample_rate,
        )
        self._cmd_buffer = AudioBuffer(
            max_duration=settings.recording.max_duration,
            sample_rate=settings.audio.sample_rate,
        )

        self.state = DetectorState.IDLE
        self.running = False

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.state = DetectorState.IDLE
        log.info("Voice detector started")
        try:
            self._audio.start_stream()
            self._main_loop()
        except KeyboardInterrupt:
            log.info("Interrupted")
        finally:
            self.stop()

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self._audio.stop_stream()
        self._vad.reset()
        self._kw_buffer.clear()
        self._cmd_buffer.clear()
        log.info("Voice detector stopped")

    def _main_loop(self) -> None:
        log.info("=== Hey Clever is listening! Say 'Clever' to activate. ===")
        while self.running:
            chunk = self._audio.read_chunk()
            if chunk is None:
                time.sleep(0.01)
                continue

            if self.state == DetectorState.IDLE:
                self._handle_idle(chunk)
            elif self.state == DetectorState.LISTENING:
                self._handle_listening(chunk)
            elif self.state == DetectorState.ACTIVATED:
                self._handle_activated(chunk)

    # -- State handlers --

    def _handle_idle(self, chunk: np.ndarray) -> None:
        if self._vad.is_speech(chunk):
            self._kw_buffer.add(chunk)
            self.state = DetectorState.LISTENING
            self._silence_start: float | None = None
            log.debug("VAD: speech started")

    def _handle_listening(self, chunk: np.ndarray) -> None:
        is_speech = self._vad.is_speech(chunk)
        self._kw_buffer.add(chunk)

        if is_speech:
            self._silence_start = None
            if self._kw_buffer.duration >= self._settings.vad.max_buffer_sec:
                self._check_keyword()
            return

        if self._silence_start is None:
            self._silence_start = time.monotonic()
        elif time.monotonic() - self._silence_start >= self._settings.vad.silence_duration:
            if self._kw_buffer.duration >= self._settings.vad.min_speech_duration:
                self._check_keyword()
            else:
                log.debug("Speech too short (%.2fs), ignoring", self._kw_buffer.duration)
                self._reset_to_idle()

    def _check_keyword(self) -> None:
        audio = self._kw_buffer.get_audio()
        text = self._kw_transcription.transcribe(audio)
        log.debug("Whisper tiny heard: '%s'", text)

        detected, confidence = self._keyword.detect(text)
        if detected:
            log.info("🎤 Keyword detected (%.0f%%) in: '%s'", confidence * 100, text)
            self._enter_activated()
        else:
            log.debug("No keyword found, continuing")
            self._reset_to_idle()

    def _enter_activated(self) -> None:
        self.state = DetectorState.ACTIVATED
        self._audio.set_muted(True)
        self._cues.on_keyword_detected()
        self._audio.set_muted(False)
        self._cmd_buffer.clear()
        self._cmd_silence_start: float | None = None
        self._cmd_got_speech = False

    def _handle_activated(self, chunk: np.ndarray) -> None:
        self._cmd_buffer.add(chunk)
        block_rms = _rms(chunk)

        if block_rms > self._settings.recording.silence_threshold:
            self._cmd_got_speech = True
            self._cmd_silence_start = None
        elif self._cmd_got_speech:
            if self._cmd_silence_start is None:
                self._cmd_silence_start = time.monotonic()
            elif (
                time.monotonic() - self._cmd_silence_start
                >= self._settings.recording.silence_duration
            ):
                self._process_command()
                return

        if self._cmd_buffer.duration >= self._settings.recording.max_duration:
            self._process_command()

    def _process_command(self) -> None:
        self.state = DetectorState.PROCESSING
        self._cues.on_recording_done()

        audio = self._cmd_buffer.get_audio()
        duration = len(audio) / self._settings.audio.sample_rate

        if duration < self._settings.recording.min_duration or not self._cmd_got_speech:
            log.info("Recording too short or no speech (%.2fs)", duration)
            self._reset_to_idle()
            return

        log.info("Recorded %.1fs, transcribing...", duration)
        text = self._cmd_transcription.transcribe(audio)

        if not text.strip():
            log.info("Empty transcription, returning to listening")
            self._reset_to_idle()
            return

        log.info("Transcribed: '%s'", text)
        self._cues.on_processing()

        response = self._gateway.send(text)
        log.info("Response: '%s'", response[:200])

        self.state = DetectorState.RESPONDING
        self._cues.on_response_ready()
        self._audio.set_muted(True)
        self._tts.speak(response)
        self._audio.set_muted(False)

        log.info("=== Ready for next keyword ===")
        self._reset_to_idle()

    def _reset_to_idle(self) -> None:
        self.state = DetectorState.IDLE
        self._kw_buffer.clear()
        self._cmd_buffer.clear()
        self._vad.reset()
