"""Clawdbot gateway adapter using OpenAI-compatible chat completions API."""

from __future__ import annotations

import logging

import requests

from hey_clever.config.settings import GatewayConfig
from hey_clever.ports.gateway import IGateway

log = logging.getLogger(__name__)


class ClawdbotGateway(IGateway):
    def __init__(self, config: GatewayConfig) -> None:
        self._config = config

    def send(self, message: str, context: list[dict[str, str]] | None = None) -> str:
        url = f"{self._config.url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._config.token}",
            "x-clawdbot-agent-id": "main",
        }
        messages: list[dict[str, str]] = []
        if context:
            messages.extend(context)
        messages.append(
            {
                "role": "user",
                "content": (
                    "[Voice input from microphone — respond concisely for TTS playback. "
                    "Match the user's language (English or Portuguese).]\n\n" + message
                ),
            }
        )
        payload = {
            "model": "clawdbot:main",
            "user": "voice-clever",
            "messages": messages,
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=self._config.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.error("Gateway request failed: %s", e)
            return "Sorry, I couldn't process that request."
